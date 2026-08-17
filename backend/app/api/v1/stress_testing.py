from datetime import date

from app.auth.dependencies import PermissionChecker
from app.auth.permissions import RISK_READ, STRESS_EXECUTE
from app.db.database import get_db
from app.db.models import StressScenario, StressTestRun
from app.risk_engine.stress_testing import (
    StressComparisonRequest,
    StressComparisonResponse,
    StressRunRequest,
    StressRunResponse,
    StressScenarioCreate,
    StressScenarioResponse,
    StressScenarioUpdate,
    StressTestingError,
    compare_scenarios,
    run_portfolio_stress_test,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/stress-scenarios", response_model=list[StressScenarioResponse], dependencies=[Depends(PermissionChecker(RISK_READ))])
def list_scenarios(db: Session = Depends(get_db)):
    return db.query(StressScenario).all()

@router.get("/stress-scenarios/{scenario_id}", response_model=StressScenarioResponse, dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scen = db.query(StressScenario).filter(StressScenario.id == scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scen

@router.post("/stress-scenarios", response_model=StressScenarioResponse, dependencies=[Depends(PermissionChecker(STRESS_EXECUTE))])
def create_scenario(req: StressScenarioCreate, db: Session = Depends(get_db)):
    if req.rate_2y_shock_bps == 0 and req.ig_spread_shock_bps == 0 and req.hy_spread_shock_bps == 0 and req.rate_10y_shock_bps == 0 and req.rate_5y_shock_bps == 0 and req.rate_30y_shock_bps == 0:
         raise HTTPException(status_code=400, detail="At least one shock must be non-zero")
         
    if req.rate_2y_shock_bps < -2000 or req.rate_2y_shock_bps > 2000:
         raise HTTPException(status_code=400, detail="Shock boundaries exceeded")
         
    scen = StressScenario(**req.dict(exclude_unset=True))
    db.add(scen)
    try:
        db.commit()
        db.refresh(scen)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    return scen

@router.patch("/stress-scenarios/{scenario_id}", response_model=StressScenarioResponse, dependencies=[Depends(PermissionChecker(STRESS_EXECUTE))])
def update_scenario(scenario_id: int, req: StressScenarioUpdate, db: Session = Depends(get_db)):
    scen = db.query(StressScenario).filter(StressScenario.id == scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if scen.is_predefined:
        raise HTTPException(status_code=400, detail="Cannot modify predefined scenario")
        
    for k, v in req.dict(exclude_unset=True).items():
        setattr(scen, k, v)
        
    db.commit()
    db.refresh(scen)
    return scen

@router.delete("/stress-scenarios/{scenario_id}", dependencies=[Depends(PermissionChecker(STRESS_EXECUTE))])
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scen = db.query(StressScenario).filter(StressScenario.id == scenario_id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if scen.is_predefined:
        raise HTTPException(status_code=400, detail="Cannot delete predefined scenario")
    db.delete(scen)
    db.commit()
    return {"detail": "Deleted"}

@router.post("/stress-tests/portfolios/{portfolio_id}/run", response_model=StressRunResponse, dependencies=[Depends(PermissionChecker(STRESS_EXECUTE))])
def run_stress_test(
    portfolio_id: int,
    req: StressRunRequest,
    db: Session = Depends(get_db)
):
    try:
        return run_portfolio_stress_test(db, portfolio_id, req.scenario_id, date.today(), req.calculation_method)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except StressTestingError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/stress-tests/portfolios/{portfolio_id}/compare", response_model=StressComparisonResponse, dependencies=[Depends(PermissionChecker(STRESS_EXECUTE))])
def compare_stress_tests(
    portfolio_id: int,
    req: StressComparisonRequest,
    db: Session = Depends(get_db)
):
    try:
        return compare_scenarios(db, portfolio_id, req.scenario_ids, date.today())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stress-tests/runs/{run_id}", dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(StressTestRun).filter(StressTestRun.id == run_id).first()
    if not run:
         raise HTTPException(status_code=404, detail="Run not found")
         
    # Manual serialization since it involves relationships
    positions = []
    from app.db.models import Portfolio, StressPositionResult
    portfolio = db.query(Portfolio).filter(Portfolio.id == run.portfolio_id).first()
    bonds_map = {p.bond_id: p.bond for p in portfolio.positions}
    
    positions_results = db.query(StressPositionResult).filter(StressPositionResult.stress_test_run_id == run.id).all()
    for pos in positions_results:
        b = bonds_map.get(pos.bond_id)
        positions.append({
            "id": pos.id,
            "bond_id": pos.bond_id,
            "bond_name": b.bond_name if b else "Unknown",
            "issuer": b.issuer_name if b else "Unknown",
            "rating": getattr(b, "credit_rating", "NR") or "NR",
            "sector": getattr(b, "sector", "Unknown") or "Unknown",
            "base_clean_price": float(pos.base_clean_price),
            "stressed_clean_price": float(pos.stressed_clean_price),
            "base_market_value": float(pos.base_market_value),
            "stressed_market_value": float(pos.stressed_market_value),
            "rate_shock_bps": float(pos.rate_shock_bps),
            "spread_shock_bps": float(pos.spread_shock_bps),
            "pnl": float(pos.pnl),
            "pnl_percent": float(pos.pnl_percent),
            "contribution_percent": float(pos.pnl / run.base_market_value * 100) if run.base_market_value != 0 else 0
        })
        
    return {
        "id": run.id,
        "portfolio_id": run.portfolio_id,
        "scenario_id": run.scenario_id,
        "valuation_date": run.valuation_date.isoformat(),
        "calculation_method": run.calculation_method,
        "base_market_value": float(run.base_market_value),
        "stressed_market_value": float(run.stressed_market_value),
        "total_pnl": float(run.total_pnl),
        "total_loss_percent": float(run.total_loss_percent),
        "position_count": run.position_count,
        "positions": positions
    }

@router.get("/stress-tests/portfolios/{portfolio_id}/history", dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_portfolio_stress_history(
    portfolio_id: int, 
    limit: int = Query(10), 
    db: Session = Depends(get_db)
):
    runs = db.query(StressTestRun).filter(StressTestRun.portfolio_id == portfolio_id).order_by(StressTestRun.created_at.desc()).limit(limit).all()
    results = []
    for r in runs:
        results.append({
            "id": r.id,
            "scenario_id": r.scenario_id,
            "valuation_date": r.valuation_date.isoformat(),
            "calculation_method": r.calculation_method,
            "total_pnl": float(r.total_pnl),
            "total_loss_percent": float(r.total_loss_percent),
            "created_at": r.created_at.isoformat()
        })
    return results
