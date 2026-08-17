from datetime import date, datetime

from pydantic import BaseModel


class PipelineRunRequest(BaseModel):
    run_type: str = "INCREMENTAL" # INCREMENTAL, BACKFILL
    dataset_key: str | None = None
    category: str | None = None
    start_date: date | None = None
    end_date: date | None = None

class PipelineJobRunResponse(BaseModel):
    id: int
    pipeline_run_id: int
    dataset_key: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    rows_fetched: int
    rows_inserted: int
    rows_updated: int
    rows_rejected: int
    retry_count: int
    error_message: str | None = None

    class Config:
        from_attributes = True

class PipelineRunResponse(BaseModel):
    id: int
    run_type: str
    status: str
    requested_start_date: date | None = None
    requested_end_date: date | None = None
    started_at: datetime
    completed_at: datetime | None = None
    triggered_by: str
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    error_summary: str | None = None
    job_runs: list[PipelineJobRunResponse] | None = None

    class Config:
        from_attributes = True
