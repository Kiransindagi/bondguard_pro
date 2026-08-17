from datetime import datetime

from pydantic import BaseModel


class DataQualityResultResponse(BaseModel):
    id: int
    data_quality_run_id: int
    dataset_key: str
    check_name: str
    status: str
    observed_value: float | None = None
    expected_value: float | None = None
    message: str | None = None

    class Config:
        from_attributes = True

class DataQualityRunResponse(BaseModel):
    id: int
    pipeline_run_id: int | None = None
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    datasets_checked: int
    checks_passed: int
    checks_warned: int
    checks_failed: int
    results: list[DataQualityResultResponse] | None = None

    class Config:
        from_attributes = True

class DatasetQualitySummary(BaseModel):
    dataset_key: str
    category: str
    source: str
    status: str
    latest_check_date: datetime | None = None
