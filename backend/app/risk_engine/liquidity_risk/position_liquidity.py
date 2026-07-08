from decimal import Decimal
from typing import Dict, Any
from .types import LiquidityAssumptionConfig, StressScenarioType
from .classification import classify_liquidity
from .liquidity_score import calculate_liquidity_score
from .transaction_cost import estimate_bid_ask_spread_bps, calculate_liquidation_cost
from .liquidation_horizon import estimate_daily_capacity, calculate_days_to_liquidate, get_horizon_bucket
from .stressed_liquidity import get_stressed_multipliers

def calculate_position_liquidity(
    bond_type: str, 
    rating: str, 
    years_to_maturity: float, 
    market_value: Decimal, 
    portfolio_weight: float,
    config: LiquidityAssumptionConfig,
    scenario: StressScenarioType = StressScenarioType.NORMAL
) -> Dict[str, Any]:
    
    score = calculate_liquidity_score(bond_type, rating, years_to_maturity, portfolio_weight, config)
    l_class = classify_liquidity(score)
    
    spread_mult, cap_mult = get_stressed_multipliers(scenario, bond_type)
    
    base_spread = estimate_bid_ask_spread_bps(bond_type, rating, config)
    spread = base_spread * spread_mult
    
    cost = calculate_liquidation_cost(market_value, spread)
    
    base_cap = estimate_daily_capacity(bond_type, rating, config)
    capacity = base_cap * cap_mult
    
    if scenario == StressScenarioType.NORMAL:
        part_rate = config.participation_rate_normal
    elif scenario == StressScenarioType.MODERATE:
        part_rate = config.participation_rate_conservative
    else:
        part_rate = config.participation_rate_stressed
        
    raw_days, trading_days = calculate_days_to_liquidate(float(market_value), capacity, part_rate)
    bucket = get_horizon_bucket(trading_days)
    
    return {
        'liquidity_score': score,
        'liquidity_class': l_class.value,
        'estimated_bid_ask_bps': spread,
        'estimated_liquidation_cost': cost,
        'model_daily_capacity': Decimal(str(capacity)),
        'participation_rate': part_rate,
        'raw_days_to_liquidate': raw_days,
        'estimated_trading_days_to_liquidate': trading_days,
        'liquidation_horizon_bucket': bucket.value
    }
