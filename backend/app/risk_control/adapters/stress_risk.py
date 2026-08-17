from datetime import date
from decimal import Decimal

from app.risk_control.enums import MetricType
from app.risk_control.types import NormalizedMetricResult
from sqlalchemy.orm import Session


class StressRiskAdapter:
    def get_value(self, metric: MetricType, portfolio_id: int, valuation_date: date, db: Session) -> NormalizedMetricResult:
        from app.risk_engine.stress_testing.portfolio_stress import compare_scenarios
        
        try:
            from app.db.models import StressScenario
            predefined = db.query(StressScenario).filter(StressScenario.is_predefined.is_(True)).all()
            val = None
            
            if predefined:
                scenario_ids = [s.id for s in predefined]
                comparison = compare_scenarios(db, portfolio_id, scenario_ids, valuation_date)
                if comparison and comparison.scenarios:
                    if metric == MetricType.WORST_STRESS_LOSS:
                        worst = comparison.scenarios[0]
                        total_pnl = worst.total_pnl
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
