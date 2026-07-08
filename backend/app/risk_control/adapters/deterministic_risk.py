from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal
from app.risk_control.enums import MetricType
from app.risk_control.types import NormalizedMetricResult
from app.risk_control.metric_registry import MetricAdapter

class DeterministicRiskAdapter:
    def get_value(self, metric: MetricType, portfolio_id: int, valuation_date: date, db: Session) -> NormalizedMetricResult:
        from app.api.v1.risk import get_portfolio_risk_summary
        
        try:
            metrics = get_portfolio_risk_summary(portfolio_id, valuation_date, db)
            val = None
            if metrics:
                if metric == MetricType.PORTFOLIO_MARKET_VALUE:
                    val = metrics.total_market_value
                elif metric == MetricType.PORTFOLIO_MODIFIED_DURATION:
                    val = metrics.weighted_modified_duration
                elif metric == MetricType.TOTAL_DV01:
                    val = metrics.total_dv01
            
            return NormalizedMetricResult(
                metric_type=metric.value,
                value=val,
                unit="USD" if metric in (MetricType.PORTFOLIO_MARKET_VALUE, MetricType.TOTAL_DV01) else "years",
                calculation_source="DETERMINISTIC_PRICING",
                model_status="AVAILABLE" if val is not None else "UNAVAILABLE",
                limitations=None,
                valuation_date=valuation_date,
                metadata={}
            )
        except Exception as e:
            return NormalizedMetricResult(
                metric_type=metric.value,
                value=None,
                unit="N/A",
                calculation_source="DETERMINISTIC_PRICING",
                model_status="ERROR",
                limitations=str(e),
                valuation_date=valuation_date,
                metadata={}
            )

adapter = DeterministicRiskAdapter()

def register_deterministic_metrics(registry):
    registry.register(MetricType.PORTFOLIO_MARKET_VALUE, adapter)
    registry.register(MetricType.PORTFOLIO_MODIFIED_DURATION, adapter)
    registry.register(MetricType.TOTAL_DV01, adapter)
