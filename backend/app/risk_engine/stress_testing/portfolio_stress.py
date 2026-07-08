from typing import List
from datetime import date
from sqlalchemy.orm import Session
from app.db.models import StressScenario, StressTestRun
from .types import PortfolioStressSummaryResponse, StressComparisonResponse
from .scenario_runner import run_portfolio_stress_test

def summarize_run(db: Session, run: StressTestRun, scenario: StressScenario) -> PortfolioStressSummaryResponse:
    largest_loss_pos = None
    largest_gain_pos = None
    min_pnl = float('inf')
    max_pnl = float('-inf')
    
    from app.db.models import StressPositionResult
    
    positions = db.query(StressPositionResult).filter(StressPositionResult.stress_test_run_id == run.id).all()
    
    for pos in positions:
        pnl = float(pos.pnl)
        if pnl < min_pnl:
            min_pnl = pnl
            largest_loss_pos = pos.bond_id
        if pnl > max_pnl:
            max_pnl = pnl
            largest_gain_pos = pos.bond_id
            
    rate_desc = f"2Y:{scenario.rate_2y_shock_bps} 5Y:{scenario.rate_5y_shock_bps} 10Y:{scenario.rate_10y_shock_bps} 30Y:{scenario.rate_30y_shock_bps}"
    credit_desc = f"IG:{scenario.ig_spread_shock_bps} HY:{scenario.hy_spread_shock_bps}"
    
    return PortfolioStressSummaryResponse(
        portfolio_id=run.portfolio_id,
        scenario_id=run.scenario_id,
        scenario_name=scenario.name,
        valuation_date=run.valuation_date,
        calculation_method=run.calculation_method,
        base_market_value=float(run.base_market_value),
        stressed_market_value=float(run.stressed_market_value),
        total_pnl=float(run.total_pnl),
        total_loss_percent=float(run.total_loss_percent),
        largest_loss_position_bond_id=largest_loss_pos,
        largest_gain_position_bond_id=largest_gain_pos,
        position_count=run.position_count,
        rate_scenario_description=rate_desc,
        credit_scenario_description=credit_desc
    )

def compare_scenarios(
    db: Session,
    portfolio_id: int,
    scenario_ids: List[int],
    valuation_date: date
) -> StressComparisonResponse:
    summaries = []
    
    for sid in scenario_ids:
        # Run or get
        run_resp = run_portfolio_stress_test(db, portfolio_id, sid, valuation_date)
        run = db.query(StressTestRun).filter(StressTestRun.id == run_resp.id).first()
        scenario = db.query(StressScenario).filter(StressScenario.id == sid).first()
        summaries.append(summarize_run(db, run, scenario))
        
    # Sort worst loss first (most negative PnL or most negative percent)
    summaries.sort(key=lambda x: x.total_pnl)
    
    return StressComparisonResponse(
        portfolio_id=portfolio_id,
        valuation_date=valuation_date,
        scenarios=summaries
    )
