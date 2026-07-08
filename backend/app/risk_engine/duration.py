from typing import List
from decimal import Decimal
from .types import CashFlow
from .cashflows import get_periods_per_year

def calculate_macaulay_duration(cashflows: List[CashFlow], ytm: Decimal, frequency: str, dirty_price: Decimal) -> Decimal:
    """
    Calculate Macaulay duration in years from discounted cash flows.
    """
    if dirty_price == 0 or not cashflows:
        return Decimal('0')

    periods_per_year = Decimal(get_periods_per_year(frequency))
    weighted_time = Decimal('0')

    for cf in cashflows:
        discount_factor = (Decimal('1') + ytm / periods_per_year) ** (cf.time_in_years * periods_per_year)
        pv_cf = cf.total_cash_flow / discount_factor
        weighted_time += cf.time_in_years * pv_cf

    return weighted_time / dirty_price

def calculate_modified_duration(macaulay_duration: Decimal, ytm: Decimal, frequency: str) -> Decimal:
    """
    Calculate modified duration from Macaulay duration and yield.
    Modified Duration = Macaulay Duration / (1 + y / m)
    """
    if macaulay_duration == 0:
        return Decimal('0')
    periods_per_year = Decimal(get_periods_per_year(frequency))
    return macaulay_duration / (Decimal('1') + ytm / periods_per_year)
