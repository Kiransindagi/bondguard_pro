from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class AnalyticsRunRequest(BaseModel):
    valuation_date: date | None = None

class AnalyticsRunResponse(BaseModel):
    id: int
    portfolio_id: int
    valuation_date: date
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    calculation_version: str | None = None
    model_status: str | None = None
    data_quality_status: str | None = None
    error_summary: str | None = None
    metadata_json: dict[str, Any] | None = None

    class Config:
        from_attributes = True
