import logging
from datetime import date, datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.observability import log_duration

from app.db.models import (
    AnalyticsRun, PortfolioRiskSnapshot, PipelineRun, DataQualityRun, Portfolio, YieldCurvePoint
)
from app.reporting.snapshot_service import SnapshotService

logger = logging.getLogger(__name__)

class AnalyticsBatchService:
    @staticmethod
    def run_batch_analytics(db: Session, portfolio_id: int, valuation_date: date) -> AnalyticsRun:
        # Check if portfolio exists
        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise ValueError(f"Portfolio ID {portfolio_id} not found")

        # Start Analytics Run record
        run = AnalyticsRun(
            portfolio_id=portfolio_id,
            valuation_date=valuation_date,
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
            calculation_version="v1.0"
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        try:
            with log_duration("analytics_batch_run", portfolio_id=portfolio_id, valuation_date=valuation_date.isoformat()):
                # Query auxiliary runs info
                latest_pipeline = db.query(PipelineRun).order_by(PipelineRun.started_at.desc()).first()
                latest_quality = db.query(DataQualityRun).order_by(DataQualityRun.started_at.desc()).first()
            
                # Fetch latest data date for metadata context
                max_curve_date = db.query(func.max(YieldCurvePoint.observation_date)).scalar()
                market_data_as_of = max_curve_date if max_curve_date else date.today()

                # Execute Authoritative snapshot service
                snapshot = SnapshotService.generate_snapshot(db, portfolio_id, valuation_date)

                # Determine statuses
                model_status = snapshot.market_risk_model_status or "AVAILABLE"
                dq_status = latest_quality.status if latest_quality else "PASS"

                # Check for partial failure logic
                if model_status in ["UNAVAILABLE", "RATE_ONLY_MODEL"]:
                    run.status = "PARTIAL_SUCCESS"
                    run.error_summary = f"Market risk model is degraded ({model_status}) due to quality gating or history gaps."
                else:
                    run.status = "SUCCESS"

                # Populate metadata
                run.model_status = model_status
                run.data_quality_status = dq_status
                run.completed_at = datetime.now(timezone.utc)
                run.metadata_json = {
                    "market_data_as_of": market_data_as_of.isoformat(),
                    "factor_history_end_date": market_data_as_of.isoformat(),
                    "pipeline_run_id": latest_pipeline.id if latest_pipeline else None,
                    "data_quality_run_id": latest_quality.id if latest_quality else None,
                    "limit_status": snapshot.overall_limit_status,
                    "open_breaches": snapshot.open_breach_count,
                    "degraded_models": snapshot.limitations.get("degraded_models", []) if snapshot.limitations else []
                }
                db.commit()
                db.refresh(run)

                # Dispatch notifications for model degradation or unavailability
                from app.notifications import NotificationDispatcher, NotificationEventType, NotificationSeverity
                if model_status == "UNAVAILABLE":
                    NotificationDispatcher.dispatch_event(
                        db=db,
                        event_type=NotificationEventType.RATE_MODEL_UNAVAILABLE,
                        severity=NotificationSeverity.SEVERE,
                        title="Rate Model UNAVAILABLE",
                        message=f"Analytics run {run.id} completed but rate model is completely UNAVAILABLE.",
                        entity_type="ANALYTICS_RUN",
                        entity_id=run.id
                    )
                elif model_status == "RATE_ONLY_MODEL":
                    NotificationDispatcher.dispatch_event(
                        db=db,
                        event_type=NotificationEventType.MODEL_DEGRADATION,
                        severity=NotificationSeverity.WARNING,
                        title="Model Degraded to RATE_ONLY_MODEL",
                        message=f"Analytics run {run.id} completed with degradation to RATE_ONLY_MODEL.",
                        entity_type="ANALYTICS_RUN",
                        entity_id=run.id
                    )

                return run

        except Exception as e:
            logger.error(f"Batch analytics failed for portfolio {portfolio_id}: {e}", exc_info=True)
            db.rollback()
            
            # Retrieve run again to set failure
            failed_run = db.query(AnalyticsRun).filter(AnalyticsRun.id == run.id).first()
            if failed_run:
                failed_run.status = "FAILED"
                failed_run.completed_at = datetime.now(timezone.utc)
                failed_run.error_summary = str(e)[:250]
                db.commit()
                db.refresh(failed_run)

                # Dispatch notification for analytics run failure
                from app.notifications import NotificationDispatcher, NotificationEventType, NotificationSeverity
                NotificationDispatcher.dispatch_event(
                    db=db,
                    event_type=NotificationEventType.ANALYTICS_FAILURE,
                    severity=NotificationSeverity.SEVERE,
                    title="Analytics Batch Run Failed",
                    message=f"Analytics run for portfolio {portfolio_id} on {valuation_date} failed: {failed_run.error_summary}",
                    entity_type="ANALYTICS_RUN",
                    entity_id=failed_run.id
                )

                return failed_run
            raise e
