import pytest
from decimal import Decimal
from datetime import date
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, RiskLimit, RiskEvaluationRun, Breach, AuditEvent, Portfolio, Bond, Position

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_risk_control.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # create portfolio
    p = Portfolio(name="Risk Test Portfolio", description="Test", created_at=date(2023, 1, 1))
    db.add(p)
    db.commit()
    
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
    db.add(limit)
    db.commit()
    
    yield db
    Base.metadata.drop_all(bind=engine)

def test_evaluate_portfolio(setup_db):
    response = client.post("/api/v1/risk-control/portfolios/1/evaluate")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["evaluated_limit_count"] >= 0

def test_get_latest_evaluation(setup_db):
    response = client.get("/api/v1/risk-control/portfolios/1/latest")
    assert response.status_code == 200
    data = response.json()
    assert "run" in data
    assert "results" in data

def test_get_history(setup_db):
    response = client.get("/api/v1/risk-control/portfolios/1/history")
    assert response.status_code == 200
    assert len(response.json()) >= 1

def test_get_breaches(setup_db):
    response = client.get("/api/v1/risk-control/portfolios/1/breaches")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_audit_events(setup_db):
    response = client.get("/api/v1/risk-control/audit-events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_deactivate_limit(setup_db):
    # limit 1 was created in setup
    response = client.delete("/api/v1/risk-control/limits/1")
    assert response.status_code == 200
    
    # verify it is deactivated
    r2 = client.get("/api/v1/risk-control/limits/1")
    assert r2.status_code == 200
    assert r2.json()["is_active"] == False

def test_report_endpoint(setup_db):
    # ensure an evaluation exists
    client.post("/api/v1/risk-control/portfolios/1/evaluate")
    
    # request report
    response = client.get("/api/v1/risk-control/portfolios/1/report")
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
    assert data["market_risk"]["model_status"] in ["RATE_ONLY_MODEL", "AVAILABLE", "ERROR"]
