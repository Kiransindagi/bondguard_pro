from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models import User, SavedScenario, SavedScenarioRun
from app.auth.dependencies import get_current_user, PermissionChecker
from app.auth.permissions import STRESS_EXECUTE, PORTFOLIO_READ
from app.scenario_lab.validator import ScenarioValidator
from app.scenario_lab.execution_service import ScenarioExecutionService
from app.scenario_lab.comparison_service import ScenarioComparisonService

router = APIRouter()

class ScenarioCreateUpdate(BaseModel):
    name: str
    rate_2y_shock_bps: int = 0
    rate_5y_shock_bps: int = 0
    rate_10y_shock_bps: int = 0
    rate_30y_shock_bps: int = 0
    ig_spread_shock_bps: int = 0
    hy_spread_shock_bps: int = 0
    is_public: bool = False

class ScenarioRunRequest(BaseModel):
    portfolio_id: int
    rate_2y_shock_bps: int = 0
    rate_5y_shock_bps: int = 0
    rate_10y_shock_bps: int = 0
    rate_30y_shock_bps: int = 0
    ig_spread_shock_bps: int = 0
    hy_spread_shock_bps: int = 0
    valuation_date: Optional[date] = None

@router.post("/run", dependencies=[Depends(PermissionChecker(STRESS_EXECUTE))])
def run_custom_scenario(
    req: ScenarioRunRequest,
    db: Session = Depends(get_db)
):
    """
    Run full-revaluation stress testing using custom temporary shock parameters.
    """
    val_date = req.valuation_date or date.today()
    shocks = req.dict(exclude={"portfolio_id", "valuation_date"})
    ScenarioValidator.validate_shocks(shocks)

    try:
        results = ScenarioExecutionService.run_saved_scenario(
            db=db,
            portfolio_id=req.portfolio_id,
            scenario_shocks=shocks,
            valuation_date=val_date
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/scenarios", dependencies=[Depends(PermissionChecker(STRESS_EXECUTE))])
def create_scenario(
    scen_in: ScenarioCreateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Save a user-defined scenario.
    """
    shocks = scen_in.dict(exclude={"name", "is_public"})
    ScenarioValidator.validate_shocks(shocks)

    db_scen = SavedScenario(
        name=scen_in.name,
        creator_user_id=current_user.id,
        rate_2y_shock_bps=scen_in.rate_2y_shock_bps,
        rate_5y_shock_bps=scen_in.rate_5y_shock_bps,
        rate_10y_shock_bps=scen_in.rate_10y_shock_bps,
        rate_30y_shock_bps=scen_in.rate_30y_shock_bps,
        ig_spread_shock_bps=scen_in.ig_spread_shock_bps,
        hy_spread_shock_bps=scen_in.hy_spread_shock_bps,
        is_public=scen_in.is_public
    )
    db.add(db_scen)
    db.commit()
    db.refresh(db_scen)
    return db_scen

@router.get("/scenarios", dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])
def get_scenarios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all scenarios visible to the user (either owned by them or marked public).
    """
    return db.query(SavedScenario).filter(
        (SavedScenario.creator_user_id == current_user.id) | (SavedScenario.is_public == True)
    ).all()

@router.get("/scenarios/{id}", dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])
def get_scenario(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scen = db.query(SavedScenario).filter(SavedScenario.id == id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if not scen.is_public and scen.creator_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this private scenario")
    return scen

@router.put("/scenarios/{id}", dependencies=[Depends(PermissionChecker(STRESS_EXECUTE))])
def update_scenario(
    id: int,
    scen_in: ScenarioCreateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scen = db.query(SavedScenario).filter(SavedScenario.id == id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if scen.creator_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update another user's scenario")

    shocks = scen_in.dict(exclude={"name", "is_public"})
    ScenarioValidator.validate_shocks(shocks)

    for k, v in scen_in.dict().items():
        setattr(scen, k, v)
    scen.version += 1

    db.commit()
    db.refresh(scen)
    return scen

@router.delete("/scenarios/{id}", dependencies=[Depends(PermissionChecker(STRESS_EXECUTE))])
def delete_scenario(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    scen = db.query(SavedScenario).filter(SavedScenario.id == id).first()
    if not scen:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if scen.creator_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete another user's scenario")

    db.delete(scen)
    db.commit()
    return {"message": "Scenario deleted"}

@router.post("/portfolios/{portfolio_id}/compare", dependencies=[Depends(PermissionChecker(STRESS_EXECUTE))])
def compare_portfolio_scenario(
    portfolio_id: int,
    scenario_id: int = Query(...),
    valuation_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run and persist a scenario comparison result.
    """
    val_date = valuation_date or date.today()
    try:
        run = ScenarioComparisonService.run_and_compare(
            db=db,
            portfolio_id=portfolio_id,
            scenario_id=scenario_id,
            valuation_date=val_date,
            user_id=current_user.id
        )
        return run
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
