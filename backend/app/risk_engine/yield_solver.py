from typing import List
from decimal import Decimal
from .types import CashFlow
from .valuation import dirty_price_from_ytm
from .exceptions import SolverError, InvalidInputError

def calculate_ytm(cashflows: List[CashFlow], dirty_price: Decimal, frequency: str, 
                  guess: float = 0.05, tol: float = 1e-8, max_iter: int = 100) -> Decimal:
    """
    Calculate Yield to Maturity (YTM) given a dirty price and cash flows.
    Uses a bisection solver internally with floats for speed, returns a Decimal.
    Yield is decimal (e.g. 0.05 for 5%).
    """
    if dirty_price <= 0:
        raise InvalidInputError("Dirty price must be positive.")
    if not cashflows:
        raise SolverError("No cash flows provided to solve YTM.")

    target_price = float(dirty_price)
    
    # Define pricing function over float for solver speed
    def price_f(y: float) -> float:
        # Avoid Decimal conversions inside the tight loop
        return float(dirty_price_from_ytm(cashflows, Decimal(str(y)), frequency))

    # Bisection bounds
    y_low = -0.99
    y_high = 10.0
    
    p_low = price_f(y_low)
    p_high = price_f(y_high)
    
    if p_low < target_price < p_high or p_high < target_price < p_low:
        # Valid bracket
        pass
    else:
        raise SolverError(f"Could not bracket the yield for price {target_price}")

    for _ in range(max_iter):
        y_mid = (y_low + y_high) / 2.0
        p_mid = price_f(y_mid)
        
        if abs(p_mid - target_price) < tol:
            return Decimal(str(round(y_mid, 8)))
            
        # Price and yield are inversely related
        if (p_mid > target_price):
            y_low = y_mid
        else:
            y_high = y_mid

    raise SolverError("YTM solver failed to converge within maximum iterations.")
