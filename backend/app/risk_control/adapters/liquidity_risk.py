from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal
from app.risk_control.enums import MetricType
from app.risk_control.types import NormalizedMetricResult

class LiquidityRiskAdapter:
    def get_value(self, metric: MetricType, portfolio_id: int, valuation_date: date, db: Session) -> NormalizedMetricResult:
        try:
            val = None
            unit = "N/A"
            limitations = "Synthetic capacity assumptions remain explicitly labeled as proxy estimates."
            
            if metric == MetricType.LIQUIDITY_ADJUSTED_VAR:
                from app.api.v1.liquidity_risk import calculate_liquidity_adjusted_var_internal
                var_data = calculate_liquidity_adjusted_var_internal(portfolio_id, db)
                if var_data:
                    val = Decimal(var_data.liquidity_adjusted_var)
                    unit = "USD"
                    limitations = "Liquidity-adjusted VaR must not imply that liquidity adjustment restores missing credit spread risk."
                    if var_data.model_status != "FULL_FACTOR_MODEL":
                        limitations += f" Original model status: {var_data.model_status}."
            else:
                from app.services.liquidity_snapshot import generate_liquidity_snapshot
                snapshot = generate_liquidity_snapshot(db, portfolio_id, valuation_date)
                if snapshot:
                    if metric == MetricType.LIQUIDITY_SCORE:
                        val = Decimal(snapshot.weighted_liquidity_score)
                        unit = "score"
                    elif metric == MetricType.LIQUIDATION_COST_BPS:
                        val = Decimal(snapshot.estimated_liquidation_cost_bps)
                        unit = "bps"
                    elif metric == MetricType.MAX_DAYS_TO_LIQUIDATE:
                        val = Decimal(snapshot.max_days_to_liquidate)
                        unit = "days"
                    elif metric == MetricType.VERY_LOW_LIQUIDITY_EXPOSURE:
                        val = Decimal(snapshot.very_low_liquidity_weight)
                        unit = "ratio"
            
            return NormalizedMetricResult(
                metric_type=metric.value,
                value=val,
                unit=unit,
                calculation_source="LIQUIDITY_PROXY",
                model_status="CHARACTERISTIC_BASED_PROXY_V1" if val is not None else "UNAVAILABLE",
                limitations=limitations,
                valuation_date=valuation_date,
                metadata={}
            )
        except Exception as e:
            return NormalizedMetricResult(
                metric_type=metric.value,
                value=None,
                unit="N/A",
                calculation_source="LIQUIDITY_PROXY",
                model_status="ERROR",
                limitations=str(e),
                valuation_date=valuation_date,
                metadata={}
            )

adapter = LiquidityRiskAdapter()

def register_liquidity_risk_metrics(registry):
    registry.register(MetricType.LIQUIDITY_SCORE, adapter)
    registry.register(MetricType.LIQUIDATION_COST_BPS, adapter)
    registry.register(MetricType.MAX_DAYS_TO_LIQUIDATE, adapter)
    registry.register(MetricType.VERY_LOW_LIQUIDITY_EXPOSURE, adapter)
    registry.register(MetricType.LIQUIDITY_ADJUSTED_VAR, adapter)
