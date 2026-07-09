from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import List, Dict, Any
from app.db.database import get_db
from app.db.models import AnalyticsRun, PortfolioRiskSnapshot
from app.schemas.analytics import AnalyticsRunRequest, AnalyticsRunResponse
from app.services.analytics_service import AnalyticsBatchService

from app.auth.dependencies import PermissionChecker
from app.auth.permissions import RISK_READ, ANALYTICS_RUN

router = APIRouter()

@router.post("/portfolios/{portfolio_id}/run", response_model=AnalyticsRunResponse, dependencies=[Depends(PermissionChecker(ANALYTICS_RUN))])
def trigger_portfolio_analytics(portfolio_id: int, req: AnalyticsRunRequest, db: Session = Depends(get_db)):
    val_date = req.valuation_date or date.today()
    try:
        run = AnalyticsBatchService.run_batch_analytics(db, portfolio_id, val_date)
        return run
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch run execution failed: {str(e)}")

@router.get("/portfolios/{portfolio_id}/latest", dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_latest_portfolio_analytics(portfolio_id: int, db: Session = Depends(get_db)):
    # Find latest successful or partial success run
    latest_run = db.query(AnalyticsRun).filter(
        AnalyticsRun.portfolio_id == portfolio_id,
        AnalyticsRun.status.in_(["SUCCESS", "PARTIAL_SUCCESS"])
    ).order_by(AnalyticsRun.started_at.desc()).first()

    if not latest_run:
        raise HTTPException(status_code=404, detail="No analytics runs found for this portfolio")

    # Fetch corresponding snapshot
    snapshot = db.query(PortfolioRiskSnapshot).filter(
        PortfolioRiskSnapshot.portfolio_id == portfolio_id,
        PortfolioRiskSnapshot.snapshot_date == latest_run.valuation_date
    ).first()

    return {
        "run": latest_run,
        "snapshot": snapshot
    }

@router.get("/portfolios/{portfolio_id}/history", response_model=List[AnalyticsRunResponse], dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_portfolio_analytics_history(portfolio_id: int, limit: int = 50, db: Session = Depends(get_db)):
    history = db.query(AnalyticsRun).filter(
        AnalyticsRun.portfolio_id == portfolio_id
    ).order_by(AnalyticsRun.started_at.desc()).limit(limit).all()
    return history

@router.get("/runs/{run_id}", response_model=AnalyticsRunResponse, dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_analytics_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(AnalyticsRun).filter(AnalyticsRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analytics run not found")
    return run

