from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import DataQualityRun, DataQualityResult
from app.schemas.data_quality import DataQualityRunResponse, DatasetQualitySummary, DataQualityResultResponse
from app.data_pipeline.registry import get_active_datasets, get_dataset_metadata
from app.data_quality.engine import DataQualityEngine

from app.auth.dependencies import PermissionChecker
from app.auth.permissions import AUDIT_READ, QUALITY_RUN

router = APIRouter()

@router.post("/run", response_model=DataQualityRunResponse, dependencies=[Depends(PermissionChecker(QUALITY_RUN))])
def trigger_quality_run(db: Session = Depends(get_db)):
    engine = DataQualityEngine(db)
    try:
        run = engine.run_quality_suite()
        return run
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data quality run failed: {str(e)}")

@router.get("/summary", response_model=DataQualityRunResponse, dependencies=[Depends(PermissionChecker(AUDIT_READ))])
def get_latest_quality_summary(db: Session = Depends(get_db)):
    latest_run = db.query(DataQualityRun).order_by(DataQualityRun.started_at.desc()).first()
    if not latest_run:
        raise HTTPException(status_code=404, detail="No data quality runs found")
    
    # Retrieve all results for the latest run
    results = db.query(DataQualityResult).filter(DataQualityResult.data_quality_run_id == latest_run.id).all()
    latest_run.results = results
    return latest_run

@router.get("/datasets", response_model=List[DatasetQualitySummary], dependencies=[Depends(PermissionChecker(AUDIT_READ))])
def get_datasets_quality_status(db: Session = Depends(get_db)):
    active_datasets = get_active_datasets()
    summaries = []

    for dataset in active_datasets:
        key = dataset["dataset_key"]
        
        # Get latest quality status for this dataset
        latest_res = db.query(DataQualityResult).filter(
            DataQualityResult.dataset_key == key
        ).order_by(DataQualityResult.id.desc()).first()
        
        status = "NO_DATA"
        latest_check_date = None
        if latest_res:
            status = latest_res.status
            # Find the run it belongs to for checking timestamp
            run = db.query(DataQualityRun).filter(DataQualityRun.id == latest_res.data_quality_run_id).first()
            if run:
                latest_check_date = run.completed_at or run.started_at

        summaries.append(DatasetQualitySummary(
            dataset_key=key,
            category=dataset["category"],
            source=dataset["source"],
            status=status,
            latest_check_date=latest_check_date
        ))
        
    return summaries

@router.get("/datasets/{dataset_key}", response_model=List[DataQualityResultResponse], dependencies=[Depends(PermissionChecker(AUDIT_READ))])
def get_dataset_quality_details(dataset_key: str, db: Session = Depends(get_db)):
    meta = get_dataset_metadata(dataset_key)
    if not meta:
        raise HTTPException(status_code=404, detail="Dataset key not found in registry")
        
    # Get latest quality run
    latest_run = db.query(DataQualityRun).order_by(DataQualityRun.started_at.desc()).first()
    if not latest_run:
        raise HTTPException(status_code=404, detail="No quality runs have been executed yet")
        
    results = db.query(DataQualityResult).filter(
        DataQualityResult.data_quality_run_id == latest_run.id,
        DataQualityResult.dataset_key == dataset_key
    ).all()
    
    return results

