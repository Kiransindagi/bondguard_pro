from decimal import Decimal

from .cashflows import get_periods_per_year
from .types import CashFlow


def calculate_convexity(cashflows: list[CashFlow], ytm: Decimal, frequency: str, dirty_price: Decimal) -> Decimal:
    """
    Calculate analytical bond convexity consistent with periodic compounding.
    """
    if dirty_price == 0 or not cashflows:
        return Decimal(0)

    periods_per_year = Decimal(get_periods_per_year(frequency))
    convexity_sum = Decimal(0)

    for cf in cashflows:
        t_periods = cf.time_in_years * periods_per_year
        discount_factor = (Decimal(1) + ytm / periods_per_year) ** (t_periods + Decimal(2))
        pv_cf = cf.total_cash_flow / discount_factor
        
        # t * (t + 1) term in periods, scaled back to years squared
        convexity_sum += (t_periods * (t_periods + Decimal(1))) * pv_cf

    # Scale back by periods_per_year squared
    return (convexity_sum / dirty_price) / (periods_per_year ** Decimal(2))
