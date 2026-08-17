from datetime import date

import pytest
from app.db.models import Portfolio, RiskLimit


@pytest.fixture(scope="function")
def setup_db(db_session):
    # create portfolio
    p = Portfolio(name="Risk Test Portfolio", description="Test", created_at=date(2023, 1, 1))
    db_session.add(p)
    db_session.commit()
    
    # create limit
    limit = RiskLimit(
        code="TEST-MAX-DUR",
        name="Test Max Duration",
        metric_type="PORTFOLIO_MODIFIED_DURATION",
        scope_type="GLOBAL",
        direction="MAXIMUM",
        warning_threshold=5.0,
        limit_threshold=7.0,
        severity="HARD_LIMIT",
        effective_from=date(2020, 1, 1),
        is_active=True
    )
    db_session.add(limit)
    db_session.commit()
    
    yield db_session

def test_evaluate_portfolio(clean_client, setup_db):
    response = clean_client.post("/api/v1/risk-control/portfolios/1/evaluate")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["evaluated_limit_count"] >= 0

def test_get_latest_evaluation(clean_client, setup_db):
    clean_client.post("/api/v1/risk-control/portfolios/1/evaluate")
    response = clean_client.get("/api/v1/risk-control/portfolios/1/latest")
    assert response.status_code == 200
    data = response.json()
    assert "run" in data
    assert "results" in data

def test_get_history(clean_client, setup_db):
    clean_client.post("/api/v1/risk-control/portfolios/1/evaluate")
    response = clean_client.get("/api/v1/risk-control/portfolios/1/history")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_get_breaches(clean_client, setup_db):
    response = clean_client.get("/api/v1/risk-control/portfolios/1/breaches")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_audit_events(clean_client, setup_db):
    response = clean_client.get("/api/v1/risk-control/audit-events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_deactivate_limit(clean_client, setup_db):
    # limit 1 was created in setup
    response = clean_client.delete("/api/v1/risk-control/limits/1")
    assert response.status_code == 200
    
    # verify it is deactivated
    r2 = clean_client.get("/api/v1/risk-control/limits/1")
    assert r2.status_code == 200
    assert r2.json()["is_active"] is False

def test_report_endpoint(clean_client, setup_db):
    # ensure an evaluation exists
    clean_client.post("/api/v1/risk-control/portfolios/1/evaluate")
    
    # request report
    response = clean_client.get("/api/v1/risk-control/portfolios/1/report")
    assert response.status_code == 200
    
    data = response.json()
    assert "portfolio" in data
    assert "report_metadata" in data
    assert "portfolio_risk" in data
    assert "market_risk" in data
    assert "stress_risk" in data
    assert "liquidity_risk" in data
    assert "concentration" in data
    assert "limit_summary" in data
    assert "limit_results" in data
    assert "breach_summary" in data
    assert "active_breaches" in data
    assert "model_governance" in data
    
    # check specific degraded markers
    assert data["market_risk"]["model_status"] in ["RATE_ONLY_MODEL", "AVAILABLE", "ERROR", "UNAVAILABLE"]


