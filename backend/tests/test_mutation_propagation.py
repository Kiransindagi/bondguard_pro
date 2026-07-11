import pytest
from decimal import Decimal
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.db.models import (
    Portfolio, Bond, Position, Transaction, YieldCurvePoint,
    CreditSpread, StressScenario, PortfolioRiskSnapshot, RiskLimit,
    RiskEvaluationRun, RiskLimitResult, Breach, LiquidityAssumption
)
from app.services.portfolio import PortfolioService
from app.services.bond import BondService
from app.services.position import PositionService
from app.risk_control import setup_risk_control
from app.risk_control.evaluator import LimitEvaluator
from app.reporting.snapshot_service import SnapshotService
from app.risk_control.reporting_service import ReportingService

@pytest.fixture(autouse=True)
def init_risk_control():
    setup_risk_control()

def test_mutation_propagation_lifecycle(client, seeded_db_session: Session):
    db = seeded_db_session

    # 1. Seed historical factor returns for 255 consecutive days to pass the 252-obs quality gate
    start_obs_date = date(2023, 1, 1)
    for i in range(260):
        obs_date = start_obs_date + timedelta(days=i)
        
        # Check yield curve points individually
        for tenor, yield_val, sid in [(2.0, 4.0, "DGS2"), (5.0, 4.2, "DGS5"), (10.0, 4.5, "DGS10"), (30.0, 4.8, "DGS30")]:
            exists = db.query(YieldCurvePoint).filter(
                YieldCurvePoint.observation_date == obs_date,
                YieldCurvePoint.tenor_years == tenor
            ).first()
            if not exists:
                db.add(YieldCurvePoint(observation_date=obs_date, tenor_years=tenor, yield_percent=yield_val, series_id=sid, source="FRED"))
            
        # Check credit spreads individually. Use 'IG' and 'HY' to satisfy unique constraint uq_credit_spread_obs
        for sid, stype, sbps in [("BAMLC0A0CM", "IG", 150.0), ("BAMLH0A0HYM2", "HY", 450.0)]:
            exists = db.query(CreditSpread).filter(
                CreditSpread.observation_date == obs_date,
                CreditSpread.spread_type == stype,
                CreditSpread.source == "FRED"
            ).first()
            if not exists:
                db.add(CreditSpread(observation_date=obs_date, series_id=sid, spread_type=stype, spread_bps=sbps, source="FRED"))
            
    db.commit()

    # 2. ADMIN creates portfolio
    port_res = client.post("/api/v1/portfolios", json={
        "name": "Integration Propagation Port",
        "description": "Verification Port",
        "base_currency": "USD",
        "benchmark": "Bloomberg US Aggregate"
    })
    assert port_res.status_code == 200
    portfolio_id = port_res.json()["id"]

    # Create a government bond
    bond_res = client.post("/api/v1/bonds", json={
        "isin": "US9999999003",
        "cusip": "999999903",
        "ticker": "T 3.0 2030",
        "issuer_name": "US Government",
        "bond_name": "US Treas 3% 2030",
        "face_value": 1000.0,
        "coupon_rate": 0.03,
        "coupon_frequency": "semiannual",
        "issue_date": "2020-01-01",
        "maturity_date": "2030-01-01",
        "day_count_convention": "30/360",
        "bond_type": "GOVERNMENT",
        "credit_rating": "AAA",
        "sector": "Sovereign",
        "country": "US"
    })
    assert bond_res.status_code == 200
    bond_id = bond_res.json()["id"]

    # Setup a global risk limit for Market Value
    limit = RiskLimit(
        code="L-MV-INTEGRATION",
        name="MV Integration Limit",
        metric_type="PORTFOLIO_MARKET_VALUE",
        scope_type="GLOBAL",
        direction="MAXIMUM",
        limit_threshold=Decimal('50000.0'),
        warning_threshold=Decimal('40000.0'),
        severity="HARD_LIMIT",
        effective_from=date(2024, 1, 1),
        is_active=True
    )
    db.add(limit)
    db.commit()

    # 3. Records BUY transaction
    # We will buy 100 units of face value 1000 at clean price 100.0.
    # Total cost = 100 * 1000 * 100 / 100 = 100,000.0
    tx1_res = client.post("/api/v1/transactions", json={
        "portfolio_id": portfolio_id,
        "bond_id": bond_id,
        "transaction_type": "BUY",
        "trade_date": "2024-01-01",
        "settlement_date": "2024-01-02",
        "quantity": 100.0,
        "clean_price": 100.0,
        "accrued_interest": 0.0,
        "total_consideration": 100000.0
    })
    assert tx1_res.status_code == 200

    # 4. Prove position quantity updates
    pos_res = client.get(f"/api/v1/portfolios/{portfolio_id}/positions")
    assert pos_res.status_code == 200
    pos_data = pos_res.json()
    assert len(pos_data) == 1
    assert float(pos_data[0]["quantity"]) == 100.0

    # 5. Prove portfolio market value updates
    sum_res = client.get(f"/api/v1/portfolios/{portfolio_id}/summary")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert float(sum_data["total_market_value"]) == 100000.0

    # 6. Prove deterministic risk updates
    risk_sum_res = client.get(f"/api/v1/risk/portfolios/{portfolio_id}/summary?valuation_date=2024-01-01")
    assert risk_sum_res.status_code == 200
    risk_sum = risk_sum_res.json()
    assert float(risk_sum["total_market_value"]) == 100000.0
    assert float(risk_sum["weighted_modified_duration"]) > 0.0

    # 7. Run evaluation FIRST so that reporting has a run to reference
    eval_res = client.post(f"/api/v1/risk-control/portfolios/{portfolio_id}/evaluate?valuation_date=2024-01-01")
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert eval_data["evaluated_limit_count"] >= 1
    assert eval_data["breach_count"] >= 1
    assert eval_data["overall_status"] == "BREACH"

    # 8. Prove stress result and reports updates
    report_res = client.get(f"/api/v1/risk-control/portfolios/{portfolio_id}/report")
    assert report_res.status_code == 200
    report_data = report_res.json()
    
    # Assert stress risk section has worst scenario
    assert report_data["stress_risk"]["worst_scenario_name"] is not None
    # Assert liquidity score is resolved
    assert report_data["liquidity_risk"]["liquidity_score"] is not None
    # Assert sector/issuer concentrations are updated
    assert report_data["concentration"]["largest_issuer_weight"] == 1.0 # 100% single issuer

    # 9. Prove snapshot persists updated state at date 2024-01-01
    snap1_res = client.post(f"/api/v1/reporting/portfolios/{portfolio_id}/snapshots?valuation_date=2024-01-01")
    assert snap1_res.status_code == 200
    snap1_data = snap1_res.json()
    assert float(snap1_data["total_market_value"]) == 100000.0
    assert snap1_data["overall_limit_status"] == "BREACH"

    # 10. Records SELL transaction on 2024-01-02 to close out or decrease position
    # SELL 80 units of face value 1000 at clean price 100.0.
    # Remaining quantity = 20
    tx2_res = client.post("/api/v1/transactions", json={
        "portfolio_id": portfolio_id,
        "bond_id": bond_id,
        "transaction_type": "SELL",
        "trade_date": "2024-01-02",
        "settlement_date": "2024-01-03",
        "quantity": 80.0,
        "clean_price": 100.0,
        "accrued_interest": 0.0,
        "total_consideration": 80000.0
    })
    assert tx2_res.status_code == 200

    # 11. Position and analytics recalculate (Market value should drop to 20,000)
    pos_res_2 = client.get(f"/api/v1/portfolios/{portfolio_id}/positions")
    assert float(pos_res_2.json()[0]["quantity"]) == 20.0

    sum_res_2 = client.get(f"/api/v1/portfolios/{portfolio_id}/summary")
    assert float(sum_res_2.json()["total_market_value"]) == 20000.0

    # Next evaluation on 2024-01-02 should clear the breach (since 20k <= 50k limit)
    eval_res_2 = client.post(f"/api/v1/risk-control/portfolios/{portfolio_id}/evaluate?valuation_date=2024-01-02")
    assert eval_res_2.json()["overall_status"] == "PASS"

    # Generate next snapshot on 2024-01-02
    snap2_res = client.post(f"/api/v1/reporting/portfolios/{portfolio_id}/snapshots?valuation_date=2024-01-02")
    assert snap2_res.status_code == 200
    snap2_data = snap2_res.json()
    assert float(snap2_data["total_market_value"]) == 20000.0
    assert snap2_data["overall_limit_status"] == "PASS"

    # 12. Prove previous historical snapshot on 2024-01-01 remains unchanged
    snap1_db = db.query(PortfolioRiskSnapshot).filter(
        PortfolioRiskSnapshot.portfolio_id == portfolio_id,
        PortfolioRiskSnapshot.snapshot_date == date(2024, 1, 1)
    ).first()
    assert snap1_db is not None
    assert float(snap1_db.total_market_value) == 100000.0
    assert snap1_db.overall_limit_status == "BREACH"
