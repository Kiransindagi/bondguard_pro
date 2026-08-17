from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TransactionBase(BaseModel):
    portfolio_id: int
    bond_id: int
    transaction_type: str = Field(..., pattern="^(BUY|SELL|ADJUSTMENT)$")
    trade_date: date
    settlement_date: date | None = None
    quantity: Decimal
    clean_price: Decimal = Field(..., gt=0)
    accrued_interest: Decimal | None = Field(default=Decimal('0.0'))
    total_consideration: Decimal | None = None

    @model_validator(mode='after')
    def check_dates_and_quantities(self):
        if self.settlement_date is not None and self.settlement_date < self.trade_date:
            raise ValueError('settlement_date cannot precede trade_date')
        if self.transaction_type in ("BUY", "SELL") and self.quantity <= 0:
            raise ValueError('quantity must be greater than 0 for BUY/SELL transactions')
        if self.transaction_type == "ADJUSTMENT" and self.quantity == 0:
            raise ValueError('quantity cannot be 0 for ADJUSTMENT transactions')
        return self

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
