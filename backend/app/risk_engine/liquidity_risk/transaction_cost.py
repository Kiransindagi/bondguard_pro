from .types import LiquidityAssumptionConfig
from decimal import Decimal

def estimate_bid_ask_spread_bps(bond_type: str, rating: str, config: LiquidityAssumptionConfig) -> float:
    t = bond_type.upper()
    if 'TREASURY' in t or 'GOVERNMENT' in t:
        return config.base_spread_bps_treasury
    
    if not rating:
        return config.base_spread_bps_hy

    r = rating.upper()
    if r in ['AAA', 'AA+', 'AA', 'AA-', 'A+', 'A', 'A-', 'BBB+', 'BBB', 'BBB-']:
        return config.base_spread_bps_ig
    else:
        return config.base_spread_bps_hy

def calculate_liquidation_cost(market_value: Decimal, spread_bps: float) -> Decimal:
    """Calculates half-spread cost for liquidation."""
    return market_value * Decimal(str(spread_bps)) / Decimal('20000.0')
