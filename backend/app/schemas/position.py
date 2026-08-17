from datetime import datetime
from decimal import Decimal

from app.schemas.bond import BondResponse
from pydantic import BaseModel, ConfigDict


class PositionBase(BaseModel):
    portfolio_id: int
    bond_id: int
    quantity: Decimal
    average_cost: Decimal
    current_clean_price: Decimal | None = None
    market_value: Decimal | None = None
    unrealized_pnl: Decimal | None = None

class PositionResponse(PositionBase):
    id: int
    updated_at: datetime
    bond: BondResponse

    model_config = ConfigDict(from_attributes=True)
