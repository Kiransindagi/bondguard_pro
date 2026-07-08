class LiquidityRiskError(Exception):
    """Base exception for liquidity risk engine."""
    pass

class InvalidAssumptionError(LiquidityRiskError):
    """Raised when an invalid assumption is provided."""
    pass

class ConcentrationLimitError(LiquidityRiskError):
    """Raised for errors in concentration limits."""
    pass
