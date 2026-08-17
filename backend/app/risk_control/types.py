from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class NormalizedMetricResult(BaseModel):
    metric_type: str
    value: Decimal | None
    unit: str
    calculation_source: str
    model_status: str
    limitations: str | None
    valuation_date: date
    metadata: dict[str, Any]
