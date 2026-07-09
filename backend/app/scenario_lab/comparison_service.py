from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.models import SavedScenario, SavedScenarioRun
from app.scenario_lab.execution_service import ScenarioExecutionService
from app.scenario_lab.scenario_builder import ScenarioBuilder
from app.risk_engine.stress_testing.types import CalculationMethod

class ScenarioComparisonService:
    @staticmethod
    def run_and_compare(
        db: Session,
        portfolio_id: int,
        scenario_id: int,
        valuation_date: date,
        user_id: int,
        method: CalculationMethod = CalculationMethod.FULL_REVALUATION
    ) -> SavedScenarioRun:
        """
        Compares a portfolio against a saved scenario and persists the result.
        """
        scenario = db.query(SavedScenario).filter(SavedScenario.id == scenario_id).first()
        if not scenario:
            raise ValueError("Scenario not found")

        shocks = ScenarioBuilder.build_shock_dict(scenario)

        results = ScenarioExecutionService.run_saved_scenario(
            db=db,
            portfolio_id=portfolio_id,
            scenario_shocks=shocks,
            valuation_date=valuation_date,
            method=method
        )

        run = SavedScenarioRun(
            scenario_id=scenario.id,
            portfolio_id=portfolio_id,
            valuation_date=valuation_date,
            executed_by_user_id=user_id,
            base_market_value=Decimal(str(results["base_market_value"])),
            stressed_market_value=Decimal(str(results["stressed_market_value"])),
            pnl_impact=Decimal(str(results["pnl_impact"]))
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
