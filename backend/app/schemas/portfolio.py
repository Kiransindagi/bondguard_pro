from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal

class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_currency: str = "USD"
    benchmark: Optional[str] = None

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_currency: Optional[str] = None
    benchmark: Optional[str] = None

class PortfolioResponse(PortfolioBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PortfolioSummaryResponse(PortfolioResponse):
    total_market_value: Decimal
    total_unrealized_pnl: Decimal
    position_count: int
