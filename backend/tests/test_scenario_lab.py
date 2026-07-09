import pytest
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import Bond, Position, Portfolio
from app.scenario_lab.validator import ScenarioValidator
from app.scenario_lab.execution_service import ScenarioExecutionService


def test_custom_shock_validator():
    # Valid shocks should not raise
    valid_shocks = {
        "rate_2y_shock_bps": 50,
        "rate_5y_shock_bps": 0,
        "rate_10y_shock_bps": -100,
        "rate_30y_shock_bps": 300,
        "ig_spread_shock_bps": 50,
        "hy_spread_shock_bps": 100
    }
    ScenarioValidator.validate_shocks(valid_shocks)

    # Too high shock (> 1000 bps)
    invalid_shocks1 = {"rate_2y_shock_bps": 1200}
    with pytest.raises(ValueError) as exc:
        ScenarioValidator.validate_shocks(invalid_shocks1)
    assert "exceeds validation bounds" in str(exc.value)

    # NaN / Inf
    invalid_shocks2 = {"rate_2y_shock_bps": float('nan')}
    with pytest.raises(ValueError) as exc:
        ScenarioValidator.validate_shocks(invalid_shocks2)
    assert "cannot be NaN or Infinity" in str(exc.value)


def test_scenario_zero_shock(db_session: Session):
    """Zero shocks across all tenors and spreads must produce near-zero P&L impact."""
    treasury = Bond(isin="US123", bond_name="T-Bond", issuer_name="US Govt",
                    face_value=Decimal(100), coupon_rate=Decimal(0.04),
                    coupon_frequency="semiannual", issue_date=date(2020, 1, 1),
                    maturity_date=date(2030, 1, 1), day_count_convention="ACT/ACT",
                    bond_type="Treasury")
    corp = Bond(isin="US456", bond_name="Corp-Bond", issuer_name="Corp Inc",
                face_value=Decimal(100), coupon_rate=Decimal(0.05),
                coupon_frequency="semiannual", issue_date=date(2020, 1, 1),
                maturity_date=date(2030, 1, 1), day_count_convention="30/360",
                bond_type="Corporate")
    db_session.add_all([treasury, corp])
    db_session.commit()

    portfolio = Portfolio(name="Test Port")
    db_session.add(portfolio)
    db_session.commit()

    pos1 = Position(portfolio_id=portfolio.id, bond_id=treasury.id,
                    quantity=Decimal(1000), current_clean_price=Decimal(100))
    pos2 = Position(portfolio_id=portfolio.id, bond_id=corp.id,
                    quantity=Decimal(1000), current_clean_price=Decimal(100))
    db_session.add_all([pos1, pos2])
    db_session.commit()

    val_date = date(2024, 1, 1)
    zero_shocks = {"rate_2y_shock_bps": 0, "rate_5y_shock_bps": 0,
                   "rate_10y_shock_bps": 0, "rate_30y_shock_bps": 0,
                   "ig_spread_shock_bps": 0, "hy_spread_shock_bps": 0}
    result = ScenarioExecutionService.run_saved_scenario(db_session, portfolio.id, zero_shocks, val_date)
    assert abs(result["pnl_impact"]) < 0.01


def test_scenario_rate_increase_produces_negative_pnl(db_session: Session):
    """Parallel +100bps rate increase must produce negative P&L for long duration portfolio."""
    treasury = Bond(isin="US223", bond_name="T-Bond2", issuer_name="US Govt",
                    face_value=Decimal(100), coupon_rate=Decimal(0.04),
                    coupon_frequency="semiannual", issue_date=date(2020, 1, 1),
                    maturity_date=date(2030, 1, 1), day_count_convention="ACT/ACT",
                    bond_type="Treasury")
    corp = Bond(isin="US556", bond_name="Corp-Bond2", issuer_name="Corp Inc",
                face_value=Decimal(100), coupon_rate=Decimal(0.05),
                coupon_frequency="semiannual", issue_date=date(2020, 1, 1),
                maturity_date=date(2030, 1, 1), day_count_convention="30/360",
                bond_type="Corporate")
    db_session.add_all([treasury, corp])
    db_session.commit()

    portfolio = Portfolio(name="Duration Port")
    db_session.add(portfolio)
    db_session.commit()

    pos1 = Position(portfolio_id=portfolio.id, bond_id=treasury.id,
                    quantity=Decimal(1000), current_clean_price=Decimal(100))
    pos2 = Position(portfolio_id=portfolio.id, bond_id=corp.id,
                    quantity=Decimal(1000), current_clean_price=Decimal(100))
    db_session.add_all([pos1, pos2])
    db_session.commit()

    val_date = date(2024, 1, 1)
    rate_shocks = {"rate_2y_shock_bps": 100, "rate_5y_shock_bps": 100,
                   "rate_10y_shock_bps": 100, "rate_30y_shock_bps": 100,
                   "ig_spread_shock_bps": 0, "hy_spread_shock_bps": 0}
    result = ScenarioExecutionService.run_saved_scenario(db_session, portfolio.id, rate_shocks, val_date)
    assert result["pnl_impact"] < -100


def test_scenario_spread_widening_only_hits_corporate(db_session: Session):
    """IG spread widening must produce zero impact on Treasuries and negative on corporates."""
    treasury = Bond(isin="US323", bond_name="T-Bond3", issuer_name="US Govt",
                    face_value=Decimal(100), coupon_rate=Decimal(0.04),
                    coupon_frequency="semiannual", issue_date=date(2020, 1, 1),
                    maturity_date=date(2030, 1, 1), day_count_convention="ACT/ACT",
                    bond_type="Treasury")
    corp = Bond(isin="US656", bond_name="Corp-Bond3", issuer_name="Corp Inc",
                face_value=Decimal(100), coupon_rate=Decimal(0.05),
                coupon_frequency="semiannual", issue_date=date(2020, 1, 1),
                maturity_date=date(2030, 1, 1), day_count_convention="30/360",
                bond_type="Corporate")
    db_session.add_all([treasury, corp])
    db_session.commit()

    portfolio = Portfolio(name="Spread Port")
    db_session.add(portfolio)
    db_session.commit()

    pos1 = Position(portfolio_id=portfolio.id, bond_id=treasury.id,
                    quantity=Decimal(1000), current_clean_price=Decimal(100))
    pos2 = Position(portfolio_id=portfolio.id, bond_id=corp.id,
                    quantity=Decimal(1000), current_clean_price=Decimal(100))
    db_session.add_all([pos1, pos2])
    db_session.commit()

    val_date = date(2024, 1, 1)
    spread_shocks = {"rate_2y_shock_bps": 0, "rate_5y_shock_bps": 0,
                     "rate_10y_shock_bps": 0, "rate_30y_shock_bps": 0,
                     "ig_spread_shock_bps": 100, "hy_spread_shock_bps": 100}
    result = ScenarioExecutionService.run_saved_scenario(db_session, portfolio.id, spread_shocks, val_date)

    pos_treasury = next(p for p in result["positions"] if p["bond_id"] == treasury.id)
    pos_corp = next(p for p in result["positions"] if p["bond_id"] == corp.id)

    # Treasury has zero spread sensitivity
    assert abs(pos_treasury["pnl_impact"]) < 0.01
    # Corporate feels the spread shock
    assert pos_corp["pnl_impact"] < -10
