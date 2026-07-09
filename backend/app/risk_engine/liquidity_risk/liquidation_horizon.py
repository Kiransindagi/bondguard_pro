import math
from .types import LiquidityAssumptionConfig, HorizonBucket

def estimate_daily_capacity(bond_type: str, rating: str, config: LiquidityAssumptionConfig) -> float:
    t = bond_type.upper()
    if 'TREASURY' in t or 'GOVERNMENT' in t:
        return config.base_capacity_treasury
    
    if not rating:
        return config.base_capacity_hy

    r = rating.upper()
    if r in ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-', 'BBB+', 'BBB', 'BBB-']:
        return config.base_capacity_ig
    else:
        return config.base_capacity_hy

def calculate_days_to_liquidate(market_value: float, daily_capacity: float, participation_rate: float) -> (float, int):
    if market_value <= 0:
        return 0.0, 1
    if daily_capacity <= 0 or participation_rate <= 0:
        return 999.0, 999
    
    allowed_daily = daily_capacity * participation_rate
    raw_days = market_value / allowed_daily
    trading_days = max(1, math.ceil(raw_days))
    return float(raw_days), trading_days

def get_horizon_bucket(trading_days: int) -> HorizonBucket:
    if trading_days <= 1:
        return HorizonBucket.ONE_DAY
    elif trading_days <= 5:
        return HorizonBucket.TWO_TO_FIVE_DAYS
    elif trading_days <= 10:
        return HorizonBucket.SIX_TO_TEN_DAYS
    elif trading_days <= 20:
        return HorizonBucket.ELEVEN_TO_TWENTY_DAYS
    else:
        return HorizonBucket.OVER_TWENTY_DAYS
