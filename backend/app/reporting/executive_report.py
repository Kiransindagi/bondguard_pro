from sqlalchemy.orm import Session
from datetime import date
from app.db.models import PortfolioRiskSnapshot, Portfolio

class ExecutiveReportService:
    @staticmethod
    def generate_report(db: Session, portfolio_id: int, snapshot_date: date) -> dict:
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise ValueError("Portfolio not found")
            
        snapshot = db.query(PortfolioRiskSnapshot).filter(
            PortfolioRiskSnapshot.portfolio_id == portfolio_id,
            PortfolioRiskSnapshot.snapshot_date == snapshot_date
        ).first()
        
        if not snapshot:
            raise ValueError(f"No risk snapshot found for date {snapshot_date}")
            
        prev_snapshot = db.query(PortfolioRiskSnapshot).filter(
            PortfolioRiskSnapshot.portfolio_id == portfolio_id,
            PortfolioRiskSnapshot.snapshot_date < snapshot_date
        ).order_by(PortfolioRiskSnapshot.snapshot_date.desc()).first()
        
        from app.reporting.historical_comparison import compare_snapshots
        historical_change = compare_snapshots(snapshot, prev_snapshot)
        
        # We need active breaches from current state
        # We can either fetch them from DB or fetch from `ReportingService`
        # To get the real detailed active breaches, we call ReportingService 
        # (It's slightly inefficient to re-evaluate, but we know snapshot generation did it today)
        # However, Executive Report is supposed to be deterministic and based on snapshot where possible.
        # But for active_breaches array with notes etc, we fetch from Breach table.
        from app.db.models import Breach, RiskLimit
        breaches = db.query(Breach).filter(
            Breach.portfolio_id == portfolio_id,
            Breach.status.in_(["OPEN", "ACKNOWLEDGED"])
        ).all()
        
        active_breaches = []
        for b in breaches:
            b_limit = db.query(RiskLimit).filter(RiskLimit.id == b.risk_limit_id).first()
            if b_limit:
                active_breaches.append({
                    "breach_id": b.id,
                    "limit_code": b_limit.code,
                    "metric_type": b_limit.metric_type,
                    "severity": b.severity,
                    "status": b.status,
                    "observed_value": float(b.observed_value),
                    "threshold_value": float(b.threshold_value),
                    "breach_amount": float(b.breach_amount),
                    "opened_at": b.opened_at.isoformat() if b.opened_at else None,
                    "acknowledged_at": b.acknowledged_at.isoformat() if b.acknowledged_at else None,
                    "assigned_to": b.assigned_to
                })
        
        largest_contributor = "N/A"
        if snapshot.largest_issuer_concentration:
            largest_contributor = f"{snapshot.largest_issuer_concentration * 100:.1f}% Issuer"
            
        executive_summary = {
            "overall_risk_status": snapshot.overall_limit_status,
            "number_of_open_breaches": snapshot.open_breach_count,
            "largest_risk_contributor": largest_contributor,
            "worst_stress_scenario": snapshot.worst_stress_scenario,
            "liquidity_status": "Proxy" if snapshot.liquidity_model_type == "CHARACTERISTIC_BASED_PROXY_V1" else "Unknown",
            "market_risk_model_status": snapshot.market_risk_model_status
        }
        
        return {
            "report_metadata": {
                "snapshot_date": snapshot_date.isoformat(),
                "generated_at": snapshot.valuation_timestamp.isoformat(),
                "portfolio_id": portfolio_id
            },
            "portfolio": {
                "name": portfolio.name,
                "base_currency": portfolio.base_currency
            },
            "executive_summary": executive_summary,
            "portfolio_risk": {
                "total_market_value": float(snapshot.total_market_value),
                "total_unrealized_pnl": float(snapshot.total_unrealized_pnl),
                "weighted_ytm": snapshot.weighted_ytm,
                "weighted_modified_duration": snapshot.weighted_modified_duration,
                "total_dv01": float(snapshot.total_dv01)
            },
            "market_risk": {
                "historical_var_95_1d": float(snapshot.historical_var_95_1d) if snapshot.historical_var_95_1d else None,
                "parametric_var_95_1d": float(snapshot.parametric_var_95_1d) if snapshot.parametric_var_95_1d else None,
                "expected_shortfall_95_1d": float(snapshot.expected_shortfall_95_1d) if snapshot.expected_shortfall_95_1d else None
            },
            "stress_testing": {
                "worst_scenario": snapshot.worst_stress_scenario,
                "worst_loss": float(snapshot.worst_stress_loss) if snapshot.worst_stress_loss else None
            },
            "liquidity_risk": {
                "liquidity_score": snapshot.weighted_liquidity_score,
                "liquidation_cost_bps": snapshot.liquidation_cost_bps,
                "max_days_to_liquidate": snapshot.max_days_to_liquidate
            },
            "concentration_risk": {
                "largest_issuer": snapshot.largest_issuer_concentration,
                "largest_sector": snapshot.largest_sector_concentration
            },
            "risk_control": {
                "overall_status": snapshot.overall_limit_status,
                "open_breaches": snapshot.open_breach_count,
                "acknowledged_breaches": snapshot.acknowledged_breach_count
            },
            "active_breaches": active_breaches,
            "model_governance": snapshot.limitations,
            "historical_change": historical_change
        }
