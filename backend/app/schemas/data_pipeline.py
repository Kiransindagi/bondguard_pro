from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List

class PipelineRunRequest(BaseModel):
    run_type: str = "INCREMENTAL" # INCREMENTAL, BACKFILL
    dataset_key: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class PipelineJobRunResponse(BaseModel):
    id: int
    pipeline_run_id: int
    dataset_key: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    rows_fetched: int
    rows_inserted: int
    rows_updated: int
    rows_rejected: int
    retry_count: int
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class PipelineRunResponse(BaseModel):
    id: int
    run_type: str
    status: str
    requested_start_date: Optional[date] = None
    requested_end_date: Optional[date] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    triggered_by: str
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    error_summary: Optional[str] = None
    job_runs: Optional[List[PipelineJobRunResponse]] = None

    class Config:
        from_attributes = True
