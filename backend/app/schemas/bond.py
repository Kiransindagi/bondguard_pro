import re
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class BondBase(BaseModel):
    isin: str = Field(..., description="ISIN")
    cusip: str | None = None
    ticker: str | None = None
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
    credit_rating: str | None = None
    sector: str | None = None
    country: str | None = None

    @field_validator('isin')
    @classmethod
    def validate_isin(cls, v: str) -> str:
        if not re.match(r"^[A-Z]{2}[A-Z0-9]{9}\d$", v):
            raise ValueError("Invalid ISIN format: must be 2 uppercase letters, 9 alphanumeric characters, and 1 digit")
        return v

    @field_validator('cusip')
    @classmethod
    def validate_cusip(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^[A-Z0-9]{9}$", v):
            raise ValueError("Invalid CUSIP format: must be 9 alphanumeric characters")
        return v

    @field_validator('issuer_name', 'bond_name', 'bond_type')
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()

    @model_validator(mode='after')
    def check_dates(self):
        if self.maturity_date <= self.issue_date:
            raise ValueError('maturity_date must be after issue_date')
        return self

class BondCreate(BondBase):
    pass

class BondUpdate(BaseModel):
    issuer_name: str | None = None
    bond_name: str | None = None
    credit_rating: str | None = None
    sector: str | None = None
    country: str | None = None

    @field_validator('issuer_name', 'bond_name', 'credit_rating', 'sector', 'country')
    @classmethod
    def validate_non_empty_optional(cls, v: str | None, info) -> str | None:
        if v is not None and (not v or not v.strip()):
            raise ValueError(f"{info.field_name} cannot be empty if provided")
        return v.strip() if v is not None else None

class BondResponse(BondBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
