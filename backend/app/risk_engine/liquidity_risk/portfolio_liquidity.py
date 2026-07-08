from typing import List, Dict, Any
from decimal import Decimal
from .types import LiquidityClass

def aggregate_portfolio_liquidity(position_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_mv = sum(Decimal(str(r['market_value'])) for r in position_results)
    if total_mv <= 0:
        return {
            'portfolio_market_value': Decimal('0'),
            'weighted_liquidity_score': 0.0,
            'estimated_total_liquidation_cost': Decimal('0'),
            'estimated_total_liquidation_cost_bps': 0.0,
            'weighted_days_to_liquidate': 0.0,
            'maximum_days_to_liquidate': 0,
            'high_liquidity_weight': 0.0,
            'medium_liquidity_weight': 0.0,
            'low_liquidity_weight': 0.0,
            'very_low_liquidity_weight': 0.0,
            'very_low_liquidity_market_value': Decimal('0'),
            'largest_illiquid_position': None
        }

    w_score = 0.0
    w_days = 0.0
    max_days = 0
    total_cost = Decimal('0')
    
    classes = {c.value: Decimal('0') for c in LiquidityClass}
    
    largest_illiquid = None
    max_illiquid_mv = Decimal('0')

    for r in position_results:
        mv = Decimal(str(r['market_value']))
        weight = float(mv / total_mv)
        
        w_score += r['liquidity_score'] * weight
        w_days += r['raw_days_to_liquidate'] * weight
        
        if r['estimated_trading_days_to_liquidate'] > max_days:
            max_days = r['estimated_trading_days_to_liquidate']
            
        total_cost += r['estimated_liquidation_cost']
        classes[r['liquidity_class']] += mv
        
        if r['liquidity_class'] == LiquidityClass.VERY_LOW.value:
            if mv > max_illiquid_mv:
                max_illiquid_mv = mv
                largest_illiquid = r.get('bond_name', str(r.get('bond_id')))

    cost_bps = float(total_cost / total_mv * Decimal('10000.0')) if total_mv > 0 else 0.0
    
    return {
        'portfolio_market_value': total_mv,
        'weighted_liquidity_score': w_score,
        'estimated_total_liquidation_cost': total_cost,
        'estimated_total_liquidation_cost_bps': cost_bps,
        'weighted_days_to_liquidate': w_days,
        'maximum_days_to_liquidate': max_days,
        'high_liquidity_weight': float(classes[LiquidityClass.HIGH.value] / total_mv),
        'medium_liquidity_weight': float(classes[LiquidityClass.MEDIUM.value] / total_mv),
        'low_liquidity_weight': float(classes[LiquidityClass.LOW.value] / total_mv),
        'very_low_liquidity_weight': float(classes[LiquidityClass.VERY_LOW.value] / total_mv),
        'very_low_liquidity_market_value': classes[LiquidityClass.VERY_LOW.value],
        'largest_illiquid_position': largest_illiquid
    }
