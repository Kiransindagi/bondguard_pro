from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal
from app.risk_control.enums import MetricType
from app.risk_control.types import NormalizedMetricResult

class StressRiskAdapter:
    def get_value(self, metric: MetricType, portfolio_id: int, valuation_date: date, db: Session) -> NormalizedMetricResult:
        from app.risk_engine.stress_testing.portfolio_stress import compare_scenarios
        from app.api.v1.risk import get_portfolio_positions_risk
        
        try:
            from app.db.models import StressScenario
            predefined = db.query(StressScenario).filter(StressScenario.is_predefined == True).all()
            val = None
            
            if predefined:
                position_risks = get_portfolio_positions_risk(portfolio_id, valuation_date, db)
                comparison = compare_scenarios(db, portfolio_id, valuation_date, predefined, position_risks, "FULL_REVALUATION")
                if comparison and comparison.get("scenarios"):
                    if metric == MetricType.WORST_STRESS_LOSS:
                        worst = comparison["scenarios"][0]
                        total_pnl = worst.get("total_pnl", 0)
                        val = Decimal(abs(total_pnl)) if total_pnl < 0 else Decimal(0)
                        
            return NormalizedMetricResult(
                metric_type=metric.value,
                value=val,
                unit="USD",
                calculation_source="STRESS_TESTING",
                model_status="AVAILABLE" if val is not None else "UNAVAILABLE",
                limitations=None,
                valuation_date=valuation_date,
                metadata={}
            )
        except Exception as e:
            return NormalizedMetricResult(
                metric_type=metric.value,
                value=None,
                unit="USD",
                calculation_source="STRESS_TESTING",
                model_status="ERROR",
                limitations=str(e),
                valuation_date=valuation_date,
                metadata={}
            )

adapter = StressRiskAdapter()

def register_stress_risk_metrics(registry):
    registry.register(MetricType.WORST_STRESS_LOSS, adapter)
