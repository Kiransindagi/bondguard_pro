import pytest
from datetime import date, datetime, timedelta, timezone
from fastapi import HTTPException
from pydantic import ValidationError
from unittest.mock import patch

from app.db.models import User, Role, Permission, RefreshToken, Portfolio, Breach, AuditEvent
from app.auth.password import get_password_hash
from app.auth.tokens import create_access_token
from app.auth.exceptions import CredentialsException
from app.core.config import Settings
from app.risk_control.enums import BreachStatus
from app.risk_control.audit_service import AuditService
from scripts.seed.seed_roles_permissions import seed_data as seed_security_data

@pytest.fixture(scope="function")
def seed_security(db_session):
    seed_security_data(db_session)
    yield db_session

@pytest.fixture(scope="function")
def test_users(seed_security):
    db = seed_security
    
    # Create test password
    pwd_hash = get_password_hash("password123")
    
    # Get roles
    analyst_role = db.query(Role).filter(Role.name == "ANALYST").first()
    pm_role = db.query(Role).filter(Role.name == "PORTFOLIO_MANAGER").first()
    rm_role = db.query(Role).filter(Role.name == "RISK_MANAGER").first()
    admin_role = db.query(Role).filter(Role.name == "ADMIN").first()

    # Create users
    analyst = User(username="analyst_user", email="analyst@test.com", hashed_password=pwd_hash, is_active=True, roles=[analyst_role])
    pm = User(username="pm_user", email="pm@test.com", hashed_password=pwd_hash, is_active=True, roles=[pm_role])
    rm = User(username="rm_user", email="rm@test.com", hashed_password=pwd_hash, is_active=True, roles=[rm_role])
    admin = User(username="admin_user", email="admin@test.com", hashed_password=pwd_hash, is_active=True, roles=[admin_role])
    disabled = User(username="disabled_user", email="disabled@test.com", hashed_password=pwd_hash, is_active=False, roles=[analyst_role])

    db.add_all([analyst, pm, rm, admin, disabled])
    db.commit()
    
    yield {
        "analyst": analyst,
        "pm": pm,
        "rm": rm,
        "admin": admin,
        "disabled": disabled
    }

def get_auth_headers(client, username, password="password123"):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 1-4. Login & Authentication Flow Tests
def test_valid_login(client, test_users):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "analyst_user", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

def test_invalid_password(client, test_users):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "analyst_user", "password": "wrongpassword"}
    )
    assert response.status_code == 401

def test_unknown_user(client, test_users):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent", "password": "password123"}
    )
    assert response.status_code == 401

def test_disabled_user(client, test_users):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "disabled_user", "password": "password123"}
    )
    assert response.status_code == 403
    assert "disabled" in response.json()["detail"].lower()


# 5-6. Access Token Expiration & Validation
def test_expired_access_token(client, test_users):
    # Create an expired token manually
    expired_token = create_access_token(
        data={"sub": str(test_users["analyst"].id), "username": "analyst_user", "permissions": []},
        expires_delta=timedelta(seconds=-10)
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()

def test_malformed_token(client, test_users):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer malformed.token.value"}
    )
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


# 7-10. Refresh Token Lifecycle
def test_refresh_success(client, test_users):
    # Login to get refresh token
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "analyst_user", "password": "password123"}
    )
    ref_token = login_resp.json()["refresh_token"]

    # Call refresh
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": ref_token}
    )
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()
    assert "refresh_token" in refresh_resp.json()

def test_refresh_rotation_and_reuse_revocation(client, db_session, test_users):
    # Login to get refresh token
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "analyst_user", "password": "password123"}
    )
    ref_token1 = login_resp.json()["refresh_token"]

    # First rotation (success)
    refresh_resp1 = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": ref_token1}
    )
    assert refresh_resp1.status_code == 200
    ref_token2 = refresh_resp1.json()["refresh_token"]

    # Verify ref_token1 is marked revoked (used)
    db_token1 = db_session.query(RefreshToken).filter(RefreshToken.token == ref_token1).first()
    assert db_token1.is_revoked is True

    # Re-use ref_token1 (theft scenario) -> should revoke ref_token2 and fail
    refresh_resp2 = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": ref_token1}
    )
    assert refresh_resp2.status_code == 401

    # Verify that ref_token2 has been automatically revoked as well
    db_token2 = db_session.query(RefreshToken).filter(RefreshToken.token == ref_token2).first()
    assert db_token2.is_revoked is True

def test_logout(client, db_session, test_users):
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "analyst_user", "password": "password123"}
    )
    ref_token = login_resp.json()["refresh_token"]

    logout_resp = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": ref_token}
    )
    assert logout_resp.status_code == 200

    # Assert revoked in DB
    db_token = db_session.query(RefreshToken).filter(RefreshToken.token == ref_token).first()
    assert db_token.is_revoked is True


# 11-13. RBAC Boundaries & Permissions Matrix
def test_unauthenticated_protected_route(client):
    response = client.get("/api/v1/portfolios")
    assert response.status_code == 401

def test_authenticated_but_unauthorized_route(client, test_users):
    headers = get_auth_headers(client, "analyst_user")
    # Analyst lacks portfolio:write
    response = client.post(
        "/api/v1/portfolios",
        headers=headers,
        json={"name": "New Portfolio", "base_currency": "USD"}
    )
    assert response.status_code == 403

def test_role_permissions_boundaries(client, test_users):
    # 1. Analyst Check
    analyst_headers = get_auth_headers(client, "analyst_user")
    assert client.get("/api/v1/portfolios", headers=analyst_headers).status_code == 200
    assert client.post("/api/v1/portfolios", headers=analyst_headers, json={}).status_code == 403
    assert client.post("/api/v1/risk-control/portfolios/1/evaluate", headers=analyst_headers).status_code == 403

    # 2. PM Check
    pm_headers = get_auth_headers(client, "pm_user")
    assert client.get("/api/v1/portfolios", headers=pm_headers).status_code == 200
    # Portfolio creation is permitted
    assert client.post("/api/v1/portfolios", headers=pm_headers, json={"name": "PM Portfolio", "base_currency": "USD"}).status_code == 200
    # Stress execution is permitted
    assert client.post("/api/v1/stress-tests/portfolios/1/run", headers=pm_headers, json={"scenario_id": 1, "calculation_method": "FULL_REVALUATION"}).status_code == 200
    # Breach acknowledgment is not permitted
    assert client.post("/api/v1/risk-control/breaches/1/acknowledge", headers=pm_headers).status_code == 403

    # 3. RM Check
    rm_headers = get_auth_headers(client, "rm_user")
    # Evaluate limit is permitted
    assert client.post("/api/v1/risk-control/portfolios/1/evaluate", headers=rm_headers).status_code == 200
    # Cannot write portfolios
    assert client.post("/api/v1/portfolios", headers=rm_headers, json={}).status_code == 403


# 14. Audit Event User Attribution
def test_breach_acknowledgement_attribution(client, db_session, test_users):
    from app.db.models import RiskLimit, RiskEvaluationRun
    # Seed active breach
    p = db_session.query(Portfolio).first()
    limit = db_session.query(RiskLimit).first()
    
    # Create evaluation run
    run = RiskEvaluationRun(
        portfolio_id=p.id,
        valuation_date=date.today(),
        model_status="FULL_FACTOR_MODEL",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        overall_status="BREACH",
        evaluated_limit_count=1,
        breach_count=1,
        warning_count=0
    )
    db_session.add(run)
    db_session.commit()
    
    breach = Breach(
        portfolio_id=p.id,
        risk_limit_id=limit.id,
        first_evaluation_run_id=run.id,
        latest_evaluation_run_id=run.id,
        status=BreachStatus.OPEN.value,
        severity="HARD_LIMIT",
        observed_value=20000.0,
        threshold_value=15000.0,
        breach_amount=5000.0,
        opened_at=datetime.now(timezone.utc)
    )
    db_session.add(breach)
    db_session.commit()

    rm_headers = get_auth_headers(client, "rm_user")
    
    # Acknowledge breach with RM user
    req_id = "test-req-id-1234"
    resp = client.post(
        f"/api/v1/risk-control/breaches/{breach.id}/acknowledge?note=AttributionNote",
        headers={**rm_headers, "X-Request-ID": req_id}
    )
    assert resp.status_code == 200

    # Retrieve audit event
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.event_type == "BREACH_ACKNOWLEDGED",
        AuditEvent.entity_id == breach.id
    ).first()

    assert audit is not None
    assert audit.actor == "rm_user"
    assert audit.actor_user_id == test_users["rm"].id
    assert audit.request_id == req_id


# 15-16. Pipeline & Analytics Triggers
def test_pipeline_trigger_authorization(client, test_users):
    analyst_headers = get_auth_headers(client, "analyst_user")
    # Analyst lacks pipeline:run
    assert client.post("/api/v1/data-pipeline/run", headers=analyst_headers, json={}).status_code == 403

    admin_headers = get_auth_headers(client, "admin_user")
    # Admin is allowed but will return 500 on empty parameters which proves it passed RBAC guard
    assert client.post("/api/v1/data-pipeline/run", headers=admin_headers, json={"run_type": "INCREMENTAL"}).status_code in [200, 500]

def test_analytics_trigger_authorization(client, test_users):
    analyst_headers = get_auth_headers(client, "analyst_user")
    # Analyst lacks analytics:run
    assert client.post("/api/v1/analytics/portfolios/1/run", headers=analyst_headers, json={}).status_code == 403

    rm_headers = get_auth_headers(client, "rm_user")
    # RM can trigger analytics
    assert client.post("/api/v1/analytics/portfolios/1/run", headers=rm_headers, json={"valuation_date": "2026-06-01"}).status_code in [200, 500]


# 17. Admin-only User Management
def test_admin_user_management(client, test_users):
    # Non-admin trying to list users
    rm_headers = get_auth_headers(client, "rm_user")
    assert client.get("/api/v1/admin/users", headers=rm_headers).status_code == 403

    # Admin listing users
    admin_headers = get_auth_headers(client, "admin_user")
    resp = client.get("/api/v1/admin/users", headers=admin_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 4


# 18. Role Seeding Idempotency
def test_role_seeding_idempotency(db_session):
    # Seeding once already done in fixture
    # Run seeding again
    seed_security_data(db_session)
    
    # Assert counts of roles and permissions remain correct
    assert db_session.query(Role).count() == 4
    assert db_session.query(Permission).count() == 20


# 19. Request-ID Preservation on Auth Failure
def test_request_id_preservation_on_auth_failure(client):
    req_id = "failed-auth-uuid-9999"
    resp = client.get(
        "/api/v1/portfolios",
        headers={"X-Request-ID": req_id}
    )
    assert resp.status_code == 401
    assert resp.headers.get("X-Request-ID") == req_id


# 20. Secret/Configuration Validation
def test_production_secret_validation():
    # If production and default secret is used, ValueError should raise
    with pytest.raises(ValueError):
        Settings(ENVIRONMENT="production", JWT_SECRET_KEY="DEV_SECRET_DO_NOT_USE_IN_PRODUCTION")
    
    # Production with customized secret should pass
    s = Settings(ENVIRONMENT="production", JWT_SECRET_KEY="a_very_secure_random_key_phrase_12345")
    assert s.JWT_SECRET_KEY == "a_very_secure_random_key_phrase_12345"


# 21. Existing Public Probes
def test_public_probes(client):
    # GET /health
    resp1 = client.get("/health")
    assert resp1.status_code == 200
    assert resp1.json() == {"status": "ok"}

    # GET /api/v1/status
    resp2 = client.get("/api/v1/status")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "ok"
