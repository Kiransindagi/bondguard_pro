from app.risk_control.enums import (
    MetricType,
    ScopeType,
    LimitDirection,
    LimitSeverity,
    ResultStatus,
    BreachStatus,
    EvaluationOverallStatus,
)
from app.risk_control.types import NormalizedMetricResult
from app.risk_control.metric_registry import registry
from app.risk_control.adapters.deterministic_risk import register_deterministic_metrics
from app.risk_control.adapters.market_risk import register_market_risk_metrics
from app.risk_control.adapters.stress_risk import register_stress_risk_metrics
from app.risk_control.adapters.liquidity_risk import register_liquidity_risk_metrics
from app.risk_control.adapters.concentration_risk import register_concentration_risk_metrics

__all__ = [
    "MetricType",
    "ScopeType",
    "LimitDirection",
    "LimitSeverity",
    "ResultStatus",
    "BreachStatus",
    "EvaluationOverallStatus",
    "NormalizedMetricResult",
    "registry",
    "setup_risk_control",
]

def setup_risk_control():
    register_deterministic_metrics(registry)
    register_market_risk_metrics(registry)
    register_stress_risk_metrics(registry)
    register_liquidity_risk_metrics(registry)
    register_concentration_risk_metrics(registry)
