from .types import LiquidityClass

def classify_liquidity(score: float) -> LiquidityClass:
    if score >= 80:
        return LiquidityClass.HIGH
    elif score >= 60:
        return LiquidityClass.MEDIUM
    elif score >= 30:
        return LiquidityClass.LOW
    else:
        return LiquidityClass.VERY_LOW
