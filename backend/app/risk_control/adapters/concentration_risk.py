from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal
from app.risk_control.enums import MetricType
from app.risk_control.types import NormalizedMetricResult

class ConcentrationRiskAdapter:
    def get_value(self, metric: MetricType, portfolio_id: int, valuation_date: date, db: Session) -> NormalizedMetricResult:
        from app.api.v1.liquidity_risk import get_portfolio_concentration
        
        dim_map = {
            MetricType.ISSUER_CONCENTRATION_MAX: "issuer",
            MetricType.SECTOR_CONCENTRATION_MAX: "sector",
            MetricType.COUNTRY_CONCENTRATION_MAX: "country",
            MetricType.RATING_CONCENTRATION_MAX: "rating",
            MetricType.MAXIMUM_SINGLE_POSITION_WEIGHT: "bond_id"
        }
        
        try:
            val = None
            if metric in dim_map:
                dimension = dim_map[metric]
                concs = get_portfolio_concentration(portfolio_id, dimension, db)
                if concs and concs.breakdown:
                    val = Decimal(concs.breakdown[0].portfolio_weight)
                    
            return NormalizedMetricResult(
                metric_type=metric.value,
                value=val,
                unit="ratio",
                calculation_source="CONCENTRATION_ANALYTICS",
                model_status="AVAILABLE" if val is not None else "UNAVAILABLE",
                limitations=None,
                valuation_date=valuation_date,
                metadata={}
            )
        except Exception as e:
            return NormalizedMetricResult(
                metric_type=metric.value,
                value=None,
                unit="ratio",
                calculation_source="CONCENTRATION_ANALYTICS",
                model_status="ERROR",
                limitations=str(e),
                valuation_date=valuation_date,
                metadata={}
            )

adapter = ConcentrationRiskAdapter()

def register_concentration_risk_metrics(registry):
    registry.register(MetricType.ISSUER_CONCENTRATION_MAX, adapter)
    registry.register(MetricType.SECTOR_CONCENTRATION_MAX, adapter)
    registry.register(MetricType.COUNTRY_CONCENTRATION_MAX, adapter)
    registry.register(MetricType.RATING_CONCENTRATION_MAX, adapter)
    registry.register(MetricType.MAXIMUM_SINGLE_POSITION_WEIGHT, adapter)
