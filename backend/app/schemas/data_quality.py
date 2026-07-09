from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class DataQualityResultResponse(BaseModel):
    id: int
    data_quality_run_id: int
    dataset_key: str
    check_name: str
    status: str
    observed_value: Optional[float] = None
    expected_value: Optional[float] = None
    message: Optional[str] = None

    class Config:
        from_attributes = True

class DataQualityRunResponse(BaseModel):
    id: int
    pipeline_run_id: Optional[int] = None
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    datasets_checked: int
    checks_passed: int
    checks_warned: int
    checks_failed: int
    results: Optional[List[DataQualityResultResponse]] = None

    class Config:
        from_attributes = True

class DatasetQualitySummary(BaseModel):
    dataset_key: str
    category: str
    source: str
    status: str
    latest_check_date: Optional[datetime] = None
