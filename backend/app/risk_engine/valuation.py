from decimal import Decimal

from .cashflows import get_periods_per_year
from .types import CashFlow


def dirty_price_from_ytm(cashflows: list[CashFlow], ytm: Decimal, frequency: str) -> Decimal:
    """
    Calculate the dirty price of a bond from its yield to maturity.
    Uses standard periodic compounding based on the coupon frequency.
    Yield is decimal (e.g. 5% = 0.05).
    """
    if not cashflows:
        return Decimal(0)
        
    periods_per_year = Decimal(get_periods_per_year(frequency))
    price = Decimal(0)
    
    # Standard periodic compounding: CF / (1 + ytm/periods_per_year) ^ (t_years * periods_per_year)
    for cf in cashflows:
        discount_factor = (Decimal(1) + ytm / periods_per_year) ** (cf.time_in_years * periods_per_year)
        price += cf.total_cash_flow / discount_factor
        
    return price

def clean_price_from_ytm(cashflows: list[CashFlow], ytm: Decimal, frequency: str, accrued_interest: Decimal) -> Decimal:
    """
    Calculate the clean price of a bond from its yield to maturity.
    """
    dirty = dirty_price_from_ytm(cashflows, ytm, frequency)
    return dirty - accrued_interest
