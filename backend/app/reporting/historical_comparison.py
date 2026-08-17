from decimal import Decimal
from typing import Any

from app.db.models import PortfolioRiskSnapshot


def _safe_pct(curr: Decimal | None, prev: Decimal | None) -> float | None:
    if curr is None or prev is None:
        return None
    if prev == 0:
        return None
    return float((curr - prev) / abs(prev) * 100)

def _safe_diff(curr: Decimal | None, prev: Decimal | None) -> float | None:
    if curr is None or prev is None:
        return None
    return float(curr - prev)

def compare_snapshots(current: PortfolioRiskSnapshot, previous: PortfolioRiskSnapshot | None) -> dict[str, Any]:
    if not previous:
        return {}

    return {
        'market_value': {
            'current': float(current.total_market_value),
            'previous': float(previous.total_market_value),
            'absolute_change': float(current.total_market_value - previous.total_market_value),
            'percentage_change': _safe_pct(current.total_market_value, previous.total_market_value)
        },
        'modified_duration': {
            'current': current.weighted_modified_duration,
            'previous': previous.weighted_modified_duration,
            'absolute_change': current.weighted_modified_duration - previous.weighted_modified_duration,
            'percentage_change': _safe_pct(Decimal(current.weighted_modified_duration), Decimal(previous.weighted_modified_duration))
        },
        'total_dv01': {
            'current': float(current.total_dv01),
            'previous': float(previous.total_dv01),
            'absolute_change': float(current.total_dv01 - previous.total_dv01),
            'percentage_change': _safe_pct(current.total_dv01, previous.total_dv01)
        },
        'historical_var': {
            'current': float(current.historical_var_95_1d) if current.historical_var_95_1d else None,
            'previous': float(previous.historical_var_95_1d) if previous.historical_var_95_1d else None,
            'absolute_change': _safe_diff(current.historical_var_95_1d, previous.historical_var_95_1d),
            'percentage_change': _safe_pct(current.historical_var_95_1d, previous.historical_var_95_1d)
        },
        'worst_stress_loss': {
            'current': float(current.worst_stress_loss) if current.worst_stress_loss else None,
            'previous': float(previous.worst_stress_loss) if previous.worst_stress_loss else None,
            'absolute_change': _safe_diff(current.worst_stress_loss, previous.worst_stress_loss),
            'percentage_change': _safe_pct(current.worst_stress_loss, previous.worst_stress_loss)
        },
        'liquidity_score': {
            'current': current.weighted_liquidity_score,
            'previous': previous.weighted_liquidity_score,
            'absolute_change': current.weighted_liquidity_score - previous.weighted_liquidity_score if current.weighted_liquidity_score and previous.weighted_liquidity_score else None,
            'percentage_change': None
        },
        'open_breaches': {
            'current': current.open_breach_count,
            'previous': previous.open_breach_count,
            'absolute_change': current.open_breach_count - previous.open_breach_count,
            'percentage_change': None
        }
    }
