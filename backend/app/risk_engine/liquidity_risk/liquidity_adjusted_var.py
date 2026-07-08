def calculate_liquidity_adjusted_var(market_var: float, liquidation_cost: float) -> float:
    """Additive Liquidity-Adjusted VaR"""
    return market_var + liquidation_cost
