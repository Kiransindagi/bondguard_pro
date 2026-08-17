class LiquidityRiskError(Exception):
    """Base exception for liquidity risk engine."""

class InvalidAssumptionError(LiquidityRiskError):
    """Raised when an invalid assumption is provided."""

class ConcentrationLimitError(LiquidityRiskError):
    """Raised for errors in concentration limits."""
