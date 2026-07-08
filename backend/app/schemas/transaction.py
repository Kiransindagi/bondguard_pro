from pydantic import BaseModel, ConfigDict, Field, model_validator
from datetime import date, datetime
from decimal import Decimal

class TransactionBase(BaseModel):
    portfolio_id: int
    bond_id: int
    transaction_type: str = Field(..., pattern="^(BUY|SELL)$")
    trade_date: date
    settlement_date: date
    quantity: Decimal = Field(..., gt=0)
    clean_price: Decimal = Field(..., gt=0)
    accrued_interest: Decimal = Field(default=Decimal('0.0'))
    total_consideration: Decimal

    @model_validator(mode='after')
    def check_dates(self):
        if self.settlement_date < self.trade_date:
            raise ValueError('settlement_date cannot precede trade_date')
        return self

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
