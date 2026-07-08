import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db.database import Base
from app.main import app
from app.db.models import Portfolio, RiskLimit, RiskEvaluationRun, RiskLimitResult, Breach, AuditEvent
from app.risk_control.enums import BreachStatus, MetricType, LimitDirection, ResultStatus
from app.risk_control.metric_registry import registry
from app.risk_control.types import NormalizedMetricResult

engine = create_engine('sqlite:///:memory:')
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[app.dependency_overrides.get('get_db')] = get_test_db

client = TestClient(app)

@pytest.fixture(scope='module')
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    p = Portfolio(name='Test Portfolio', description='Test')
    db.add(p)
    db.commit()
    db.refresh(p)
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

# Add tests here

class MockAdapter:
    def __init__(self, val, unit='USD', model_status='AVAILABLE'):
        self.val = val
        self.unit = unit
        self.model_status = model_status
    def get_value(self, metric, portfolio_id, valuation_date, db):
        if self.model_status == 'ERROR':
            raise Exception('Adapter error')
        return NormalizedMetricResult(metric_type=metric.value, value=self.val, unit=self.unit, calculation_source='MOCK', model_status=self.model_status, limitations=None, valuation_date=valuation_date)

def test_limit_resolution(db_session):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)

    l1 = RiskLimit(code='L1', metric_type='TOTAL_DV01', scope_type='GLOBAL', direction='MAXIMUM', warning_threshold=50, limit_threshold=100, is_active=True, effective_from=yesterday)
    l2 = RiskLimit(code='L2', metric_type='TOTAL_DV01', scope_type='PORTFOLIO', scope_value='1', direction='MAXIMUM', warning_threshold=40, limit_threshold=80, is_active=True, effective_from=yesterday)
    l3 = RiskLimit(code='L3', metric_type='TOTAL_DV01', scope_type='GLOBAL', direction='MAXIMUM', limit_threshold=200, is_active=False, effective_from=yesterday)
    l4 = RiskLimit(code='L4', metric_type='TOTAL_DV01', scope_type='GLOBAL', direction='MAXIMUM', limit_threshold=300, is_active=True, effective_from=tomorrow)
    l5 = RiskLimit(code='L5', metric_type='TOTAL_DV01', scope_type='GLOBAL', direction='MAXIMUM', limit_threshold=400, is_active=True, effective_from=yesterday, effective_to=yesterday)
    
    db_session.add_all([l1, l2, l3, l4, l5])
    db_session.flush()

    from app.risk_control.limit_resolver import LimitResolver
    res = LimitResolver.resolve_applicable_limits(db_session, 1, today)
    assert len(res) == 1
    assert res[0].limit_threshold == 80 # override took precedence

    db_session.query(RiskLimit).delete()
    db_session.commit()

def test_exact_boundary(db_session):
    from app.risk_control.evaluator import LimitEvaluator
    
    l_max = RiskLimit(limit_threshold=100.0, direction='MAXIMUM')
    assert LimitEvaluator._evaluate_threshold(Decimal('100.0'), l_max) == ResultStatus.PASS
    assert LimitEvaluator._evaluate_threshold(Decimal('100.01'), l_max) == ResultStatus.BREACH

    l_min = RiskLimit(limit_threshold=50.0, direction='MINIMUM')
    assert LimitEvaluator._evaluate_threshold(Decimal('50.0'), l_min) == ResultStatus.PASS
    assert LimitEvaluator._evaluate_threshold(Decimal('49.99'), l_min) == ResultStatus.BREACH

def test_evaluation_breach_lifecycle(db_session):
    # Setup limit and adapter
    l1 = RiskLimit(code='L_LIFECYCLE', metric_type='TOTAL_DV01', scope_type='GLOBAL', direction='MAXIMUM', limit_threshold=100, is_active=True, effective_from=date.today(), severity='HARD_LIMIT')
    db_session.add(l1)
    db_session.commit()
    
    # 1. First violation
    registry.register(MetricType.TOTAL_DV01, MockAdapter(Decimal(150)))
    from app.risk_control.evaluator import LimitEvaluator
    run1 = LimitEvaluator.evaluate_portfolio(db_session, 1, date.today())
    
    breaches = db_session.query(Breach).filter(Breach.portfolio_id == 1, Breach.risk_limit_id == l1.id).all()
    assert len(breaches) == 1
    assert breaches[0].status == BreachStatus.OPEN.value
    b_id = breaches[0].id
    
    # 2. Repeated violation
    run2 = LimitEvaluator.evaluate_portfolio(db_session, 1, date.today())
    breaches2 = db_session.query(Breach).filter(Breach.portfolio_id == 1, Breach.risk_limit_id == l1.id).all()
    assert len(breaches2) == 1 # Deduplicated
    assert breaches2[0].latest_evaluation_run_id == run2.id
    
    # 3. Acknowledgement
    from app.risk_control.audit_service import AuditService
    breaches2[0].status = BreachStatus.ACKNOWLEDGED.value
    AuditService.append_event(db_session, 'BREACH_ACKNOWLEDGED', 'BREACH', b_id, 'UPDATE', {}, {})
    db_session.commit()
    
    # 4. Repeated violation after acknowledgement
    run3 = LimitEvaluator.evaluate_portfolio(db_session, 1, date.today())
    b_ack = db_session.query(Breach).filter(Breach.id == b_id).first()
    assert b_ack.status == BreachStatus.ACKNOWLEDGED.value
    
    # 5. Recovery
    registry.register(MetricType.TOTAL_DV01, MockAdapter(Decimal(90)))
    run4 = LimitEvaluator.evaluate_portfolio(db_session, 1, date.today())
    b_res = db_session.query(Breach).filter(Breach.id == b_id).first()
    assert b_res.status == BreachStatus.RESOLVED.value
    
    # 6. Re-breach
    registry.register(MetricType.TOTAL_DV01, MockAdapter(Decimal(110)))
    run5 = LimitEvaluator.evaluate_portfolio(db_session, 1, date.today())
    all_b = db_session.query(Breach).filter(Breach.portfolio_id == 1, Breach.risk_limit_id == l1.id).all()
    assert len(all_b) == 2
    assert all_b[0].status == BreachStatus.RESOLVED.value
    assert all_b[1].status == BreachStatus.OPEN.value

def test_evaluation_failure(db_session):
    registry.register(MetricType.TOTAL_DV01, MockAdapter(None, model_status='ERROR'))
    from app.risk_control.evaluator import LimitEvaluator
    
    run = LimitEvaluator.evaluate_portfolio(db_session, 1, date.today())
    
    # If adapter raises Exception, evaluation run is created as FAILED
    # Actually our mock adapter raises exception if model_status=='ERROR' when get_value is called
    assert run.overall_status == 'FAILED'
    assert run.error_message is not None

def test_api_evaluation(db_session):
    registry.register(MetricType.TOTAL_DV01, MockAdapter(Decimal(110)))
    from app.api.v1.risk_control import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    
    response = client.post('/api/v1/risk-control/portfolios/1/evaluate')
    assert response.status_code == 200
    data = response.json()
    assert data['overall_status'] == 'BREACH'
