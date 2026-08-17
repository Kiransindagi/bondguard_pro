from datetime import datetime, timezone

from app.core.config import settings
from app.db.database import get_db
from app.db.models import AnalyticsRun, DataQualityRun, PipelineRun
from app.risk_engine.market_risk.availability import check_model_availability
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

router = APIRouter()



class StatusResponse(BaseModel):
    status: str
    environment: str
    version: str
    timestamp: str

class DatabaseStatusResponse(BaseModel):
    status: str
    timestamp: str

@router.get("/status", response_model=StatusResponse)
def get_status():
    return StatusResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@router.get("/system/database", response_model=DatabaseStatusResponse)
def get_database_status(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return DatabaseStatusResponse(
            status="connected",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Database connection failed")

class OperationalHealthResponse(BaseModel):
    status: str
    database_connected: bool
    latest_pipeline_status: str | None = None
    latest_quality_status: str | None = None
    latest_analytics_run_status: str | None = None
    market_risk_model_availability: str | None = None


@router.get("/system/health", response_model=OperationalHealthResponse)
def get_operational_health(db: Session = Depends(get_db)):
    # Check DB
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    latest_pipe = db.query(PipelineRun).order_by(PipelineRun.started_at.desc()).first()
    latest_dq = db.query(DataQualityRun).order_by(DataQualityRun.started_at.desc()).first()
    latest_analytics = db.query(AnalyticsRun).order_by(AnalyticsRun.started_at.desc()).first()
    
    avail = "UNAVAILABLE"
    try:
        avail_res = check_model_availability(db)
        avail = avail_res.model_status.value
    except Exception:
        pass

    overall_status = "ok"
    if not db_ok or (latest_dq and latest_dq.status == "FAIL") or (latest_analytics and latest_analytics.status == "FAILED"):
        overall_status = "degraded"

    return OperationalHealthResponse(
        status=overall_status,
        database_connected=db_ok,
        latest_pipeline_status=latest_pipe.status if latest_pipe else None,
        latest_quality_status=latest_dq.status if latest_dq else None,
        latest_analytics_run_status=latest_analytics.status if latest_analytics else None,
        market_risk_model_availability=avail
    )
