from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal
from app.risk_control.enums import MetricType
from app.risk_control.types import NormalizedMetricResult

class MarketRiskAdapter:
    def get_value(self, metric: MetricType, portfolio_id: int, valuation_date: date, db: Session) -> NormalizedMetricResult:
        from app.api.v1.market_risk import get_historical_var, get_parametric_var, get_expected_shortfall
        
        try:
            val = None
            metadata = {}
            model_status = "AVAILABLE"
            limitations = None
            
            if metric == MetricType.HISTORICAL_VAR_95_1D:
                res = get_historical_var(portfolio_id=portfolio_id, confidence_level=0.95, horizon_days=1, db=db)
                val = Decimal(res.get("var_currency", 0))
                metadata = res
            elif metric == MetricType.PARAMETRIC_VAR_95_1D:
                res = get_parametric_var(portfolio_id=portfolio_id, confidence_level=0.95, horizon_days=1, db=db)
                val = Decimal(res.get("var_currency", 0))
                metadata = res
            elif metric == MetricType.EXPECTED_SHORTFALL_95_1D:
                res = get_expected_shortfall(portfolio_id=portfolio_id, confidence_level=0.95, db=db)
                val = Decimal(res.get("expected_shortfall_currency", 0))
                metadata = res
                
            if metadata.get("model_type"):
                model_status = metadata.get("model_type")
                if model_status != "FULL_FACTOR_MODEL":
                    limitations = metadata.get("limitations", "Missing credit spread risk")
            
            return NormalizedMetricResult(
                metric_type=metric.value,
                value=val,
                unit="USD",
                calculation_source="MARKET_RISK_SIMULATION",
                model_status=model_status,
                limitations=limitations,
                valuation_date=valuation_date,
                metadata=metadata
            )
        except Exception as e:
            return NormalizedMetricResult(
                metric_type=metric.value,
                value=None,
                unit="USD",
                calculation_source="MARKET_RISK_SIMULATION",
                model_status="ERROR",
                limitations=str(e),
                valuation_date=valuation_date,
                metadata={}
            )

adapter = MarketRiskAdapter()

def register_market_risk_metrics(registry):
    registry.register(MetricType.HISTORICAL_VAR_95_1D, adapter)
    registry.register(MetricType.PARAMETRIC_VAR_95_1D, adapter)
    registry.register(MetricType.EXPECTED_SHORTFALL_95_1D, adapter)
