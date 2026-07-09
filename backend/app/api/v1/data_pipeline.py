from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.db.models import PipelineRun
from app.schemas.data_pipeline import PipelineRunRequest, PipelineRunResponse
from app.data_pipeline.orchestrator import PipelineOrchestrator

from app.auth.dependencies import PermissionChecker
from app.auth.permissions import AUDIT_READ, PIPELINE_RUN

router = APIRouter()

@router.post("/run", response_model=PipelineRunResponse, dependencies=[Depends(PermissionChecker(PIPELINE_RUN))])
def trigger_pipeline_run(req: PipelineRunRequest, db: Session = Depends(get_db)):
    orchestrator = PipelineOrchestrator(db)
    try:
        run = orchestrator.run_pipeline(
            run_type=req.run_type,
            dataset_key=req.dataset_key,
            category=req.category,
            start_date=req.start_date,
            end_date=req.end_date,
            triggered_by="USER"
        )
        return run
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

from sqlalchemy.orm import joinedload

@router.get("/runs", response_model=List[PipelineRunResponse], dependencies=[Depends(PermissionChecker(AUDIT_READ))])
def list_pipeline_runs(limit: int = 50, db: Session = Depends(get_db)):
    runs = db.query(PipelineRun).options(joinedload(PipelineRun.job_runs)).order_by(PipelineRun.started_at.desc()).limit(limit).all()
    return runs

@router.get("/runs/{run_id}", response_model=PipelineRunResponse, dependencies=[Depends(PermissionChecker(AUDIT_READ))])
def get_pipeline_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(PipelineRun).options(joinedload(PipelineRun.job_runs)).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return run

