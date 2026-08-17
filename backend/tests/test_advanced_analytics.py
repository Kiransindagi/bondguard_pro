from datetime import date
from decimal import Decimal

import pytest
from app.db.models import Bond
from app.risk_engine.advanced_analytics import (
    AdvancedAnalyticsCalculator,
    PnLExplainCalculator,
    calculate_tenor_weights,
)
from app.risk_engine.position_risk import calculate_position_risk
from app.risk_engine.types import BondRiskInput
from sqlalchemy.orm import Session


def test_calculate_tenor_weights():
    """KRD tenor weights must sum to 1.0 and interpolate correctly."""
    # Exact boundary nodes
    w2 = calculate_tenor_weights(2.0)
    assert w2 == {"2Y": 1.0, "5Y": 0.0, "10Y": 0.0, "30Y": 0.0}

    w10 = calculate_tenor_weights(10.0)
    assert w10 == {"2Y": 0.0, "5Y": 0.0, "10Y": 1.0, "30Y": 0.0}

    # Linear interpolation midpoint
    w3 = calculate_tenor_weights(3.5)
    assert w3["2Y"] == pytest.approx(0.5)
    assert w3["5Y"] == pytest.approx(0.5)
    assert w3["10Y"] == 0.0
    assert w3["30Y"] == 0.0
    assert sum(w3.values()) == pytest.approx(1.0)

    # Beyond 30Y: extrapolated/capped to 30Y bucket
    w40 = calculate_tenor_weights(40.0)
    assert w40 == {"2Y": 0.0, "5Y": 0.0, "10Y": 0.0, "30Y": 1.0}

    # Under 2Y: capped to 2Y bucket
    w1 = calculate_tenor_weights(1.0)
    assert w1 == {"2Y": 1.0, "5Y": 0.0, "10Y": 0.0, "30Y": 0.0}


def test_bucketed_dv01_reconciliation(db_session: Session):
    """Sum of bucketed DV01s must reconcile to the base position DV01."""
    treasury = Bond(
        isin="US1234ADV", bond_name="T-Bond DV01", issuer_name="US Govt",
        face_value=Decimal(100), coupon_rate=Decimal("0.04"),
        coupon_frequency="semiannual", issue_date=date(2020, 1, 1),
        maturity_date=date(2027, 1, 1), day_count_convention="ACT/ACT",
        bond_type="Treasury"
    )
    db_session.add(treasury)
    db_session.commit()

    val_date = date(2024, 1, 1)
    buckets = AdvancedAnalyticsCalculator.calculate_bucketed_dv01(
        treasury, val_date, Decimal(100), Decimal(1)
    )

    inp = BondRiskInput(
        bond_id=treasury.id, face_value=treasury.face_value,
        coupon_rate=treasury.coupon_rate, coupon_frequency=treasury.coupon_frequency,
        issue_date=treasury.issue_date, maturity_date=treasury.maturity_date,
        day_count_convention=treasury.day_count_convention, valuation_date=val_date,
        clean_price=Decimal(100), quantity=Decimal(1)
    )
    base_risk = calculate_position_risk(inp)

    total_bucket_dv01 = sum(buckets.values())
    assert abs(total_bucket_dv01 - float(base_risk.dv01_currency)) < 0.001


def test_pnl_explain_residual(db_session: Session):
    """PnL explain residual must equal actual_pnl minus explained_pnl."""
    corp = Bond(
        isin="US4567ADV", bond_name="Corp-Bond PnL", issuer_name="Corp Inc",
        face_value=Decimal(100), coupon_rate=Decimal("0.05"),
        coupon_frequency="semiannual", issue_date=date(2020, 1, 1),
        maturity_date=date(2030, 1, 1), day_count_convention="30/360",
        bond_type="Corporate"
    )
    db_session.add(corp)
    db_session.commit()

    val_date = date(2024, 1, 1)
    result = PnLExplainCalculator.calculate_pnl_explain(
        bond=corp, valuation_date=val_date,
        clean_price=Decimal(100), quantity=Decimal(100),
        rate_shock_bps=50, spread_shock_bps=50, actual_pnl=-500
    )

    expected_residual = result["actual_pnl"] - result["explained_pnl"]
    assert abs(result["residual"] - expected_residual) < 0.01
