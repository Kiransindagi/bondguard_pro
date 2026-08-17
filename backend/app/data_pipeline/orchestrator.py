import logging
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.core.observability import log_duration
from app.data.fred_client import FredAPIClient
from app.data.market_client import YFinanceProvider
from app.data.repository import DataRepository
from app.data.transformations import (
    transform_fred_to_credit_spread,
    transform_fred_to_macro,
    transform_fred_to_yield_curve,
)
from app.data.validators import validate_market_price, validate_yield_curve_point
from app.data_pipeline.registry import get_active_datasets, get_dataset_metadata
from app.db.models import (
    CreditSpread,
    Instrument,
    MacroObservation,
    MarketPrice,
    PipelineJobRun,
    PipelineRun,
    YieldCurvePoint,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def retry_on_exception(func_call: Any, max_attempts: int = 3, initial_delay: float = 1.0) -> Any:
    """
    Exponential backoff wrapper for transient failures.
    FRED has its own tenacity configuration, so this is mainly utilized for yfinance provider.
    """
    attempt = 1
    delay = initial_delay
    while True:
        try:
            return func_call()
        except Exception as e:
            # Do not retry on validation/integrity failures that are persistent
            error_str = str(e).lower()
            if "validation" in error_str or "integrity" in error_str or "unique constraint" in error_str:
                logger.error(f"Non-retryable failure encountered: {e}")
                raise
            
            if attempt >= max_attempts:
                logger.error(f"Operation failed after {max_attempts} attempts: {e}")
                raise
            logger.warning(f"Transient error: {e}. Attempt {attempt}/{max_attempts}. Retrying in {delay}s...")
            time.sleep(delay)
            attempt += 1
            delay *= 2

class PipelineOrchestrator:
    def __init__(self, db: Session):
        self.db = db
        self.repo = DataRepository(db)
        self.fred_client = FredAPIClient()
        self.market_provider = YFinanceProvider()

    def get_max_observation_date(self, dataset_key: str) -> date | None:
        meta = get_dataset_metadata(dataset_key)
        if not meta:
            return None
        
        category = meta["category"]
        if category == "Yield_Curve":
            return self.db.query(func.max(YieldCurvePoint.observation_date)).filter(
                YieldCurvePoint.series_id == dataset_key
            ).scalar()
        elif category == "Credit_Spreads":
            # Map BAMLC0A0CM -> IG, BAMLH0A0HYM2 -> HY
            spread_type = "IG" if dataset_key == "BAMLC0A0CM" else "HY"
            return self.db.query(func.max(CreditSpread.observation_date)).filter(
                CreditSpread.spread_type == spread_type
            ).scalar()
        elif category == "Macro":
            return self.db.query(func.max(MacroObservation.observation_date)).filter(
                MacroObservation.series_id == dataset_key
            ).scalar()
        elif category == "ETF_Market_Data":
            inst = self.db.query(Instrument).filter(Instrument.symbol == dataset_key).first()
            if not inst:
                return None
            return self.db.query(func.max(MarketPrice.observation_date)).filter(
                MarketPrice.instrument_id == inst.id
            ).scalar()
        return None

    def calculate_dates(self, dataset_key: str, run_type: str, start_date: date | None = None, end_date: date | None = None) -> tuple[date | None, date | None]:
        # Resolve end date
        if not end_date:
            end_date = date.today()

        # Resolve start date
        if start_date:
            return start_date, end_date

        if run_type == "INCREMENTAL":
            max_date = self.get_max_observation_date(dataset_key)
            if max_date:
                # Next day after max date
                return max_date + timedelta(days=1), end_date
            
        # Default backfill fallback (3 years)
        return date.today() - timedelta(days=3 * 365), end_date

    def ingest_dataset_job(self, job_run: PipelineJobRun, start_date: date, end_date: date) -> dict[str, Any]:
        dataset_key = job_run.dataset_key
        meta = get_dataset_metadata(dataset_key)
        category = meta["category"]
        source = meta["source"]

        if start_date > end_date:
            logger.info(f"Dataset {dataset_key} is already up to date.")
            return {"rows_fetched": 0, "rows_inserted": 0, "status": "SUCCESS"}

        rows_fetched = 0
        rows_inserted = 0

        if source == "FRED":
            # FRED client has built-in tenacity retries. We invoke directly.
            raw_records = self.fred_client.fetch_series(dataset_key, start_date, end_date)
            rows_fetched = len(raw_records)

            if rows_fetched > 0:
                if category == "Yield_Curve":
                    transformed = transform_fred_to_yield_curve(raw_records)
                    valid = [r for r in transformed if validate_yield_curve_point(r)]
                    rows_inserted = self.repo.upsert_yield_curve_points(valid)
                elif category == "Credit_Spreads":
                    transformed = transform_fred_to_credit_spread(raw_records)
                    rows_inserted = self.repo.upsert_credit_spreads(transformed)
                elif category == "Macro":
                    transformed = transform_fred_to_macro(raw_records)
                    rows_inserted = self.repo.upsert_macro_observations(transformed)
        elif source == "yfinance":
            # yfinance provider fetch
            inst = self.repo.get_or_create_instrument(dataset_key, dataset_key)
            
            def fetch_op():
                return self.market_provider.fetch_historical_prices(dataset_key, start_date, end_date)

            raw_records = retry_on_exception(fetch_op, max_attempts=3, initial_delay=1.0)
            rows_fetched = len(raw_records)

            if rows_fetched > 0:
                valid = [r for r in raw_records if validate_market_price(r)]
                rows_inserted = self.repo.upsert_market_prices(inst.id, valid)

        return {
            "rows_fetched": rows_fetched,
            "rows_inserted": rows_inserted,
            "status": "SUCCESS"
        }

    def run_pipeline(
        self, 
        run_type: str, 
        dataset_key: str | None = None, 
        category: str | None = None, 
        start_date: date | None = None, 
        end_date: date | None = None, 
        triggered_by: str = "SYSTEM"
    ) -> PipelineRun:
        # Determine active datasets to process
        all_active = get_active_datasets()
        targets = []

        if dataset_key:
            targets = [meta for meta in all_active if meta["dataset_key"] == dataset_key]
        elif category:
            targets = [meta for meta in all_active if meta["category"] == category]
        else:
            targets = all_active

        # Initialize Pipeline Run record
        pipeline_run = PipelineRun(
            run_type=run_type,
            status="RUNNING",
            requested_start_date=start_date,
            requested_end_date=end_date,
            started_at=datetime.now(timezone.utc),
            triggered_by=triggered_by,
            total_jobs=len(targets)
        )
        self.db.add(pipeline_run)
        self.db.commit()
        self.db.refresh(pipeline_run)

        successful_jobs = 0
        failed_jobs = 0
        error_logs = []

        for target in targets:
            key = target["dataset_key"]
            job_run = PipelineJobRun(
                pipeline_run_id=pipeline_run.id,
                dataset_key=key,
                status="RUNNING",
                started_at=datetime.now(timezone.utc)
            )
            self.db.add(job_run)
            self.db.commit()
            self.db.refresh(job_run)

            try:
                # Calculate job execution start/end dates
                j_start, j_end = self.calculate_dates(key, run_type, start_date, end_date)
                
                # Execute Ingestion Job
                with log_duration("ingestion_job", dataset_key=key, pipeline_run_id=pipeline_run.id):
                    stats = self.ingest_dataset_job(job_run, j_start, j_end)

                job_run.status = "SUCCESS"
                job_run.rows_fetched = stats["rows_fetched"]
                job_run.rows_inserted = stats["rows_inserted"]
                job_run.completed_at = datetime.now(timezone.utc)
                self.db.commit()
                successful_jobs += 1
            except Exception as e:
                logger.error(f"Pipeline job for {key} failed: {e}", exc_info=True)
                job_run.status = "FAILED"
                job_run.error_message = str(e)[:250]
                job_run.completed_at = datetime.now(timezone.utc)
                self.db.commit()
                failed_jobs += 1
                error_logs.append(f"{key}: {e}")

        # Update final Pipeline status
        pipeline_run.completed_at = datetime.now(timezone.utc)
        pipeline_run.successful_jobs = successful_jobs
        pipeline_run.failed_jobs = failed_jobs

        if failed_jobs == 0:
            pipeline_run.status = "SUCCESS"
        elif successful_jobs > 0:
            pipeline_run.status = "PARTIAL_SUCCESS"
        else:
            pipeline_run.status = "FAILED"

        if error_logs:
            pipeline_run.error_summary = "; ".join(error_logs)[:400]

        self.db.commit()
        self.db.refresh(pipeline_run)

        # Dispatch notifications on failures or partial successes
        from app.notifications import (
            NotificationDispatcher,
            NotificationEventType,
            NotificationSeverity,
        )
        if pipeline_run.status == "FAILED":
            NotificationDispatcher.dispatch_event(
                db=self.db,
                event_type=NotificationEventType.PIPELINE_FAILURE,
                severity=NotificationSeverity.SEVERE,
                title="Data Pipeline Execution Failed",
                message=f"Data pipeline run {pipeline_run.id} failed completely. Error: {pipeline_run.error_summary}",
                entity_type="PIPELINE_RUN",
                entity_id=pipeline_run.id
            )
        elif pipeline_run.status == "PARTIAL_SUCCESS":
            NotificationDispatcher.dispatch_event(
                db=self.db,
                event_type=NotificationEventType.PIPELINE_PARTIAL_SUCCESS,
                severity=NotificationSeverity.WARNING,
                title="Data Pipeline Execution Partial Success",
                message=f"Data pipeline run {pipeline_run.id} succeeded with partial issues. Successful jobs: {successful_jobs}, Failed: {failed_jobs}.",
                entity_type="PIPELINE_RUN",
                entity_id=pipeline_run.id
            )

        return pipeline_run
