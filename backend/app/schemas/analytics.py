from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, Dict, Any

class AnalyticsRunRequest(BaseModel):
    valuation_date: Optional[date] = None

class AnalyticsRunResponse(BaseModel):
    id: int
    portfolio_id: int
    valuation_date: date
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    calculation_version: Optional[str] = None
    model_status: Optional[str] = None
    data_quality_status: Optional[str] = None
    error_summary: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
