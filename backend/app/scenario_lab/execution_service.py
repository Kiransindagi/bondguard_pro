from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
import logging

from app.db.models import Portfolio, SavedScenario, SavedScenarioRun
from app.risk_engine.position_risk import calculate_position_risk
from app.risk_engine.types import BondRiskInput
from app.risk_engine.stress_testing.scenario_pricing import calculate_scenario_pricing
from app.risk_engine.stress_testing.types import CalculationMethod

logger = logging.getLogger(__name__)

class ScenarioExecutionService:
    @staticmethod
    def run_saved_scenario(
        db: Session,
        portfolio_id: int,
        scenario_shocks: dict,
        valuation_date: date,
        method: CalculationMethod = CalculationMethod.FULL_REVALUATION
    ) -> dict:
        """
        Run a stress scenario on a portfolio based on custom shock parameters.
        Returns a dictionary summarizing base MV, stressed MV, and P&L impact.
        """
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise ValueError("Portfolio not found")

        rate_2y = scenario_shocks.get("rate_2y_shock_bps", 0)
        rate_5y = scenario_shocks.get("rate_5y_shock_bps", 0)
        rate_10y = scenario_shocks.get("rate_10y_shock_bps", 0)
        rate_30y = scenario_shocks.get("rate_30y_shock_bps", 0)
        ig_spread = scenario_shocks.get("ig_spread_shock_bps", 0)
        hy_spread = scenario_shocks.get("hy_spread_shock_bps", 0)

        total_base_mv = Decimal('0')
        total_stressed_mv = Decimal('0')
        position_details = []

        for pos in portfolio.positions:
            bond = pos.bond
            # Compute base position risk
            input_data = BondRiskInput(
                bond_id=bond.id,
                face_value=bond.face_value,
                coupon_rate=bond.coupon_rate,
                coupon_frequency=bond.coupon_frequency,
                issue_date=bond.issue_date,
                maturity_date=bond.maturity_date,
                day_count_convention=bond.day_count_convention,
                valuation_date=valuation_date,
                clean_price=pos.current_clean_price or Decimal('100.0'),
                quantity=pos.quantity
            )
            base_risk = calculate_position_risk(input_data)
            
            # Run stress pricing
            stressed_clean, stressed_mv = calculate_scenario_pricing(
                bond=bond,
                position=pos,
                valuation_date=valuation_date,
                base_risk=base_risk,
                rate_2y_bps=float(rate_2y),
                rate_5y_bps=float(rate_5y),
                rate_10y_bps=float(rate_10y),
                rate_30y_bps=float(rate_30y),
                ig_spread_bps=float(ig_spread),
                hy_spread_bps=float(hy_spread),
                method=method
            )

            base_mv = base_risk.market_value
            pnl_impact = stressed_mv - base_mv

            total_base_mv += base_mv
            total_stressed_mv += stressed_mv

            position_details.append({
                "bond_id": bond.id,
                "cusip": bond.cusip,
                "quantity": float(pos.quantity),
                "base_clean_price": float(base_risk.clean_price),
                "base_market_value": float(base_mv),
                "stressed_clean_price": float(stressed_clean),
                "stressed_market_value": float(stressed_mv),
                "pnl_impact": float(pnl_impact)
            })

        total_pnl = total_stressed_mv - total_base_mv

        return {
            "portfolio_id": portfolio_id,
            "base_market_value": float(total_base_mv),
            "stressed_market_value": float(total_stressed_mv),
            "pnl_impact": float(total_pnl),
            "positions": position_details
        }
