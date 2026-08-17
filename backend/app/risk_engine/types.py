from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CashFlow(BaseModel):
    payment_date: date
    coupon_amount: Decimal
    principal_amount: Decimal
    total_cash_flow: Decimal
    time_in_years: Decimal

class BondRiskInput(BaseModel):
    bond_id: int
    face_value: Decimal
    coupon_rate: Decimal
    coupon_frequency: str
    issue_date: date
    maturity_date: date
    day_count_convention: str
    valuation_date: date
    clean_price: Decimal | None = None
    ytm: Decimal | None = None
    quantity: Decimal = Decimal(1)  # for scaling position risk

class BondRiskResult(BaseModel):
    bond_id: int
    valuation_date: date
    clean_price: Decimal
    dirty_price: Decimal
    accrued_interest: Decimal
    ytm_decimal: Decimal
    macaulay_duration_years: Decimal
    modified_duration_years: Decimal
    convexity: Decimal
    dv01_currency: Decimal
    market_value: Decimal
