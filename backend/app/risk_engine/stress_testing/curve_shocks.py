import numpy as np


def interpolate_rate_shock(
    tenor_years: float,
    rate_2y_bps: float,
    rate_5y_bps: float,
    rate_10y_bps: float,
    rate_30y_bps: float
) -> float:
    """
    Interpolate the rate shock for a given tenor based on defined key rate shocks.
    Boundary rules:
    < 2Y: Flat at 2Y shock
    > 30Y: Flat at 30Y shock
    """
    tenors = np.array([2.0, 5.0, 10.0, 30.0])
    shocks = np.array([rate_2y_bps, rate_5y_bps, rate_10y_bps, rate_30y_bps])
    
    if tenor_years <= 2.0:
        return rate_2y_bps
    elif tenor_years >= 30.0:
        return rate_30y_bps
        
    return float(np.interp(tenor_years, tenors, shocks))
