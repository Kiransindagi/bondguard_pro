from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.models import Portfolio, StressScenario, StressTestRun, StressPositionResult
from app.risk_engine.types import BondRiskInput
from app.risk_engine.position_risk import calculate_position_risk
from .types import CalculationMethod, StressPositionResultResponse, StressRunResponse
from .scenario_pricing import calculate_scenario_pricing
from .curve_shocks import interpolate_rate_shock
from .spread_shocks import resolve_spread_shock
from .exceptions import StressCalculationError

def run_portfolio_stress_test(
    db: Session,
    portfolio_id: int,
    scenario_id: int,
    valuation_date: date,
    method: CalculationMethod = None
) -> StressRunResponse:
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    scenario = db.query(StressScenario).filter(StressScenario.id == scenario_id).first()
    
    if not portfolio or not scenario:
        raise ValueError("Portfolio or Scenario not found")
        
    calc_method = method or CalculationMethod(scenario.default_calculation_method)
    
    total_base_mv = Decimal('0')
    total_stressed_mv = Decimal('0')
    position_results = []
    
    try:
        for pos in portfolio.positions:
            bond = pos.bond
            # Calculate base risk
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
            
            stressed_clean, stressed_mv = calculate_scenario_pricing(
                bond=bond,
                position=pos,
                valuation_date=valuation_date,
                base_risk=base_risk,
                rate_2y_bps=scenario.rate_2y_shock_bps,
                rate_5y_bps=scenario.rate_5y_shock_bps,
                rate_10y_bps=scenario.rate_10y_shock_bps,
                rate_30y_bps=scenario.rate_30y_shock_bps,
                ig_spread_bps=scenario.ig_spread_shock_bps,
                hy_spread_bps=scenario.hy_spread_shock_bps,
                method=calc_method
            )
            
            base_mv = Decimal(str(base_risk.market_value))
            pnl = stressed_mv - base_mv
            pnl_percent = float(pnl / base_mv * 100) if base_mv != 0 else 0.0
            
            maturity_years = max(0.0, (bond.maturity_date - valuation_date).days / 365.25)
            rate_shock = interpolate_rate_shock(
                maturity_years, 
                scenario.rate_2y_shock_bps, 
                scenario.rate_5y_shock_bps, 
                scenario.rate_10y_shock_bps, 
                scenario.rate_30y_shock_bps
            )
            spread_shock = resolve_spread_shock(bond, scenario.ig_spread_shock_bps, scenario.hy_spread_shock_bps)
            
            total_base_mv += base_mv
            total_stressed_mv += stressed_mv
            
            res = StressPositionResult(
                position_id=pos.id,
                bond_id=bond.id,
                base_clean_price=Decimal(str(base_risk.clean_price)),
                stressed_clean_price=stressed_clean,
                base_market_value=base_mv,
                stressed_market_value=stressed_mv,
                pnl=pnl,
                pnl_percent=pnl_percent,
                rate_shock_bps=rate_shock,
                spread_shock_bps=spread_shock
            )
            position_results.append(res)
            
    except Exception as e:
        raise StressCalculationError(f"Calculation failed: {str(e)}")
        
    total_pnl = total_stressed_mv - total_base_mv
    total_loss_percent = float(total_pnl / total_base_mv * 100) if total_base_mv != 0 else 0.0
    
    # Persist the run atomically
    try:
        run = StressTestRun(
            portfolio_id=portfolio_id,
            scenario_id=scenario_id,
            valuation_date=valuation_date,
            calculation_method=calc_method.value,
            base_market_value=total_base_mv,
            stressed_market_value=total_stressed_mv,
            total_pnl=total_pnl,
            total_loss_percent=total_loss_percent,
            position_count=len(position_results)
        )
        db.add(run)
        db.flush()
        
        resp_positions = []
        for res in position_results:
            res.stress_test_run_id = run.id
            db.add(res)
            
            # calculate contribution percent
            contrib = float(res.pnl / total_base_mv * 100) if total_base_mv != 0 else 0.0
            bond = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first().positions[0].bond # shortcut? No.
            # properly fetch bond
            b = next(p.bond for p in portfolio.positions if p.bond.id == res.bond_id)
            
            resp_positions.append(StressPositionResultResponse(
                id=0, # temp
                bond_id=res.bond_id,
                bond_name=b.bond_name,
                issuer=b.issuer_name,
                rating=getattr(b, "credit_rating", "NR") or "NR",
                sector=getattr(b, "sector", "Unknown") or "Unknown",
                base_clean_price=float(res.base_clean_price),
                stressed_clean_price=float(res.stressed_clean_price),
                base_market_value=float(res.base_market_value),
                stressed_market_value=float(res.stressed_market_value),
                rate_shock_bps=float(res.rate_shock_bps),
                spread_shock_bps=float(res.spread_shock_bps),
                pnl=float(res.pnl),
                pnl_percent=float(res.pnl_percent),
                contribution_percent=contrib
            ))
            
        db.commit()
        
        # fix IDs after commit
        for i, res in enumerate(position_results):
            resp_positions[i].id = res.id
            
    except Exception as e:
        db.rollback()
        raise StressCalculationError(f"Persistence failed: {str(e)}")
        
    return StressRunResponse(
        id=run.id,
        portfolio_id=portfolio_id,
        scenario_id=scenario_id,
        valuation_date=valuation_date,
        calculation_method=calc_method,
        base_market_value=float(total_base_mv),
        stressed_market_value=float(total_stressed_mv),
        total_pnl=float(total_pnl),
        total_loss_percent=total_loss_percent,
        position_count=len(resp_positions),
        positions=resp_positions
    )
