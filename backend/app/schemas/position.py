from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.schemas.bond import BondResponse

class PositionBase(BaseModel):
    portfolio_id: int
    bond_id: int
    quantity: Decimal
    average_cost: Decimal
    current_clean_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None

class PositionResponse(PositionBase):
    id: int
    updated_at: datetime
    bond: BondResponse

    model_config = ConfigDict(from_attributes=True)
