from datetime import date, datetime

from app.db.models import PortfolioRiskSnapshot
from app.risk_control.reporting_service import ReportingService
from sqlalchemy.orm import Session


class SnapshotService:
    @staticmethod
    def generate_snapshot(db: Session, portfolio_id: int, valuation_date: date) -> PortfolioRiskSnapshot:
        # Ensure an evaluation run exists for this date
        from app.risk_control.evaluator import LimitEvaluator
        LimitEvaluator.evaluate_portfolio(db, portfolio_id, valuation_date)

        # Fetch the authoritative report (uses the latest run for this portfolio)
        report = ReportingService.generate_report(db, portfolio_id)

        # Check if same-day snapshot exists; upsert
        existing = db.query(PortfolioRiskSnapshot).filter(
            PortfolioRiskSnapshot.portfolio_id == portfolio_id,
            PortfolioRiskSnapshot.snapshot_date == valuation_date
        ).first()

        snapshot = existing if existing else PortfolioRiskSnapshot(
            portfolio_id=portfolio_id,
            snapshot_date=valuation_date
        )

        snapshot.valuation_timestamp = datetime.utcnow()

        # -- Portfolio Risk --
        snapshot.total_market_value = float(report.portfolio_risk.total_market_value) if report.portfolio_risk.total_market_value is not None else 0.0
        snapshot.total_unrealized_pnl = 0.0

        # Supplement with live risk summary for YTM / convexity
        try:
            from app.api.v1.risk import get_portfolio_risk_summary
            port_metrics = get_portfolio_risk_summary(portfolio_id, valuation_date, db)
            snapshot.weighted_ytm = float(port_metrics.weighted_average_ytm) if port_metrics and port_metrics.weighted_average_ytm else 0.0
            snapshot.weighted_convexity = float(port_metrics.weighted_convexity) if port_metrics and port_metrics.weighted_convexity else 0.0
        except Exception:
            snapshot.weighted_ytm = 0.0
            snapshot.weighted_convexity = 0.0

        snapshot.weighted_modified_duration = float(report.portfolio_risk.weighted_modified_duration or 0.0)
        snapshot.total_dv01 = float(report.portfolio_risk.total_dv01 or 0.0)

        # -- Market Risk --
        snapshot.historical_var_95_1d = float(report.market_risk.historical_var) if report.market_risk.historical_var is not None else None
        snapshot.expected_shortfall_95_1d = float(report.market_risk.expected_shortfall) if report.market_risk.expected_shortfall is not None else None
        snapshot.parametric_var_95_1d = float(report.market_risk.parametric_var) if report.market_risk.parametric_var is not None else None

        # -- Stress Risk --
        snapshot.worst_stress_scenario = report.stress_risk.worst_scenario_name
        snapshot.worst_stress_loss = float(report.stress_risk.pnl) if report.stress_risk.pnl is not None else None

        # -- Liquidity --
        snapshot.weighted_liquidity_score = float(report.liquidity_risk.liquidity_score) if report.liquidity_risk.liquidity_score is not None else None
        snapshot.liquidation_cost = float(report.liquidity_risk.liquidation_cost) if report.liquidity_risk.liquidation_cost is not None else None
        snapshot.liquidation_cost_bps = float(report.liquidity_risk.liquidation_cost_bps) if report.liquidity_risk.liquidation_cost_bps is not None else None
        snapshot.weighted_days_to_liquidate = float(report.liquidity_risk.weighted_days_to_liquidate) if report.liquidity_risk.weighted_days_to_liquidate is not None else None
        snapshot.max_days_to_liquidate = int(report.liquidity_risk.max_days_to_liquidate) if report.liquidity_risk.max_days_to_liquidate is not None else None

        # -- Concentration --
        snapshot.largest_issuer_concentration = float(report.concentration.largest_issuer_weight) if report.concentration.largest_issuer_weight is not None else None
        snapshot.largest_sector_concentration = float(report.concentration.largest_sector_weight) if report.concentration.largest_sector_weight is not None else None

        # -- Risk Control --
        snapshot.overall_limit_status = report.report_metadata.overall_status
        snapshot.open_breach_count = report.breach_summary.open_count
        snapshot.acknowledged_breach_count = report.breach_summary.acknowledged_count

        snapshot.market_risk_model_status = report.market_risk.model_status
        snapshot.liquidity_model_type = report.liquidity_risk.model_label

        # model_governance serialised as dict (Pydantic v2 uses model_dump)
        try:
            snapshot.limitations = report.model_governance.model_dump()
        except AttributeError:
            snapshot.limitations = report.model_governance.dict()  # fallback

        if not existing:
            db.add(snapshot)

        db.commit()
        db.refresh(snapshot)
        return snapshot
