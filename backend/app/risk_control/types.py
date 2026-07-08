from pydantic import BaseModel
from typing import Optional, Any
from datetime import date
from decimal import Decimal

class NormalizedMetricResult(BaseModel):
    metric_type: str
    value: Optional[Decimal]
    unit: str
    calculation_source: str
    model_status: str
    limitations: Optional[str]
    valuation_date: date
    metadata: dict[str, Any]
