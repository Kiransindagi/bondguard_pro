from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PortfolioBase(BaseModel):
    name: str
    description: str | None = None
    base_currency: str = "USD"
    benchmark: str | None = None
    is_active: bool = True
    status: str = "ACTIVE"

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    base_currency: str | None = None
    benchmark: str | None = None
    is_active: bool | None = None
    status: str | None = None

class PortfolioResponse(PortfolioBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PortfolioSummaryResponse(PortfolioResponse):
    total_market_value: Decimal
    total_unrealized_pnl: Decimal
    position_count: int
