from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

class BondBase(BaseModel):
    isin: str = Field(..., description="ISIN")
    cusip: Optional[str] = None
    ticker: Optional[str] = None
    issuer_name: str
    bond_name: str
    currency: str = "USD"
    face_value: Decimal = Field(..., gt=0)
    coupon_rate: Decimal = Field(..., ge=0)
    coupon_frequency: str = Field(..., pattern="^(annual|semiannual|quarterly)$")
    issue_date: date
    maturity_date: date
    day_count_convention: str = Field(..., pattern="^(ACT/ACT|ACT/360|30/360)$")
    bond_type: str
    credit_rating: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None

    @model_validator(mode='after')
    def check_dates(self):
        if self.maturity_date <= self.issue_date:
            raise ValueError('maturity_date must be after issue_date')
        return self

class BondCreate(BondBase):
    pass

class BondUpdate(BaseModel):
    issuer_name: Optional[str] = None
    bond_name: Optional[str] = None
    credit_rating: Optional[str] = None
    sector: Optional[str] = None

class BondResponse(BondBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
