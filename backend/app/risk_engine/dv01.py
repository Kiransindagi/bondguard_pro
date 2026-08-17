from decimal import Decimal

from .types import CashFlow
from .valuation import dirty_price_from_ytm


def calculate_dv01(cashflows: list[CashFlow], ytm: Decimal, frequency: str, dirty_price: Decimal, face_value: Decimal, quantity: Decimal = Decimal(1)) -> Decimal:
    """
    Calculate DV01 as the approximate currency price change for a one basis-point parallel yield move.
    DV01 is reported as a positive loss magnitude for a +1 bp yield increase.
    
    Formula using finite difference:
    DV01 = (Price(YTM - 1bp) - Price(YTM + 1bp)) / 2
    
    Position DV01 is scaled using quantity * face_value / 100
    """
    if not cashflows:
        return Decimal(0)

    bp = Decimal('0.0001')
    
    price_up = dirty_price_from_ytm(cashflows, ytm + bp, frequency)
    price_down = dirty_price_from_ytm(cashflows, ytm - bp, frequency)
    
    # Bond-level DV01 per 100 face value
    bond_dv01 = (price_down - price_up) / Decimal('2.0')
    
    # Scale to position value
    position_dv01 = bond_dv01 * quantity * face_value / Decimal('100.0')
    
    return position_dv01
