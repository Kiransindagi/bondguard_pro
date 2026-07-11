import logging
import math
from datetime import date, datetime, timezone
from typing import List, Any, Optional
from sqlalchemy.orm import Session
from app.core.observability import log_duration

from app.db.models import (
    DataQualityRun, DataQualityResult, YieldCurvePoint, 
    CreditSpread, MacroObservation, MarketPrice, Instrument
)
from app.data_pipeline.registry import get_active_datasets, get_dataset_metadata

logger = logging.getLogger(__name__)

class DataQualityEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_observations_for_dataset(self, dataset_key: str) -> List[Any]:
        meta = get_dataset_metadata(dataset_key)
        if not meta:
            return []

        category = meta["category"]
        if category == "Yield_Curve":
            return self.db.query(YieldCurvePoint).filter(
                YieldCurvePoint.series_id == dataset_key
            ).order_by(YieldCurvePoint.observation_date.asc()).all()
        elif category == "Credit_Spreads":
            spread_type = "IG" if dataset_key == "BAMLC0A0CM" else "HY"
            return self.db.query(CreditSpread).filter(
                CreditSpread.spread_type == spread_type
            ).order_by(CreditSpread.observation_date.asc()).all()
        elif category == "Macro":
            return self.db.query(MacroObservation).filter(
                MacroObservation.series_id == dataset_key
            ).order_by(MacroObservation.observation_date.asc()).all()
        elif category == "ETF_Market_Data":
            inst = self.db.query(Instrument).filter(Instrument.symbol == dataset_key).first()
            if not inst:
                return []
            return self.db.query(MarketPrice).filter(
                MarketPrice.instrument_id == inst.id
            ).order_by(MarketPrice.observation_date.asc()).all()
        return []

    def get_value_from_obs(self, obs: Any, category: str) -> Optional[float]:
        if category == "Yield_Curve":
            return obs.yield_percent
        elif category == "Credit_Spreads":
            return obs.spread_bps
        elif category == "Macro":
            return obs.value
        elif category == "ETF_Market_Data":
            return obs.close
        return None

    def run_checks_for_dataset(self, run_id: int, dataset_key: str) -> str:
        meta = get_dataset_metadata(dataset_key)
        category = meta["category"]
        tolerance = meta["freshness_tolerance"]
        min_required = meta["min_observations"]

        obs = self.get_observations_for_dataset(dataset_key)
        count = len(obs)

        # 1. Check: Freshness
        freshness_status = "PASS"
        freshness_msg = "Data is fresh."
        lag_days = None
        if count == 0:
            freshness_status = "FAIL"
            freshness_msg = "No observations found in the database."
        else:
            max_date = obs[-1].observation_date
            lag_days = (date.today() - max_date).days
            if lag_days > tolerance * 2:
                freshness_status = "FAIL"
                freshness_msg = f"Data is extremely stale. Lag: {lag_days} days, tolerance: {tolerance} days."
            elif lag_days > tolerance:
                freshness_status = "WARNING"
                freshness_msg = f"Data is stale. Lag: {lag_days} days, tolerance: {tolerance} days."

        self.save_result(run_id, dataset_key, "freshness", freshness_status, lag_days, tolerance, freshness_msg)

        if count == 0:
            return "FAIL"

        # 2. Check: Minimum History
        history_status = "PASS"
        history_msg = f"Observation count is {count}."
        if count < min_required:
            history_status = "FAIL"
            history_msg = f"Insufficient history. Found {count} observations, expected at least {min_required}."
        self.save_result(run_id, dataset_key, "min_history", history_status, count, min_required, history_msg)

        # 3. Check: Duplicates & Nulls & Negative values
        has_dup = False
        has_null = False
        has_invalid_neg = False
        has_gap = False
        has_outlier = False

        dates = [o.observation_date for o in obs]
        values = [self.get_value_from_obs(o, category) for o in obs]

        # Duplicates check
        if len(set(dates)) != len(dates):
            has_dup = True

        # Nulls and domain-invalid negative check
        for v in values:
            if v is None or math.isnan(v):
                has_null = True
            else:
                if category in ["ETF_Market_Data", "Credit_Spreads"] and v <= 0:
                    has_invalid_neg = True
                elif category in ["Yield_Curve", "Macro"] and v < -5.0:
                    has_invalid_neg = True

        # Continuity check (Business days gaps)
        for i in range(1, len(dates)):
            d1, d2 = dates[i - 1], dates[i]
            # Calculate calendar days gap
            gap = (d2 - d1).days
            # Filter weekends out approximately
            if gap > 14: # Gap of more than 2 calendar weeks
                has_gap = True
                break

        # Outliers check
        max_daily_change = 0.0
        for i in range(1, len(values)):
            v1, v2 = values[i - 1], values[i]
            if v1 is None or v2 is None:
                continue
            if category == "ETF_Market_Data":
                if v1 > 0:
                    ret = abs((v2 - v1) / v1)
                    max_daily_change = max(max_daily_change, ret)
                    if ret > 0.15: # 15% daily return limit
                        has_outlier = True
            elif category == "Credit_Spreads":
                change = abs(v2 - v1)
                max_daily_change = max(max_daily_change, change)
                if change > 300.0: # 300 bps daily spread change limit
                    has_outlier = True
            else: # Yield_Curve or Macro
                change = abs(v2 - v1)
                max_daily_change = max(max_daily_change, change)
                if change > 2.0: # 2.0% (200 bps) daily yield change limit
                    has_outlier = True

        # Save Duplicate Result
        dup_status = "FAIL" if has_dup else "PASS"
        self.save_result(run_id, dataset_key, "duplicates", dup_status, float(has_dup), 0.0, "Duplicate observation dates detected" if has_dup else "No duplicate dates.")

        # Save Null Result
        null_status = "FAIL" if has_null else "PASS"
        self.save_result(run_id, dataset_key, "nulls", null_status, float(has_null), 0.0, "Null/NaN values detected in history" if has_null else "No null values.")

        # Save Negative/Invalid Result
        neg_status = "FAIL" if has_invalid_neg else "PASS"
        self.save_result(run_id, dataset_key, "negative_values", neg_status, float(has_invalid_neg), 0.0, "Impossible or domain-invalid negative values detected" if has_invalid_neg else "Values are within valid domain.")

        # Save Continuity Result
        gap_status = "FAIL" if has_gap else "PASS"
        self.save_result(run_id, dataset_key, "continuity", gap_status, float(has_gap), 0.0, "Observation calendar gaps exceeding 2 weeks detected" if has_gap else "Observations are contiguous.")

        # Save Outliers Result
        out_status = "WARNING" if has_outlier else "PASS"
        self.save_result(run_id, dataset_key, "outliers", out_status, max_daily_change, 0.0, f"Outlier change detected: {max_daily_change:.4f}" if has_outlier else "No extreme outliers.")

        # Aggregate Dataset Status
        statuses = [freshness_status, history_status, dup_status, null_status, neg_status, gap_status, out_status]
        if "FAIL" in statuses:
            return "FAIL"
        elif "WARNING" in statuses:
            return "WARNING"
        return "PASS"

    def save_result(self, run_id: int, key: str, check_name: str, status: str, observed: Optional[float], expected: Optional[float], message: str):
        res = DataQualityResult(
            data_quality_run_id=run_id,
            dataset_key=key,
            check_name=check_name,
            status=status,
            observed_value=observed,
            expected_value=expected,
            message=message
        )
        self.db.add(res)
        self.db.commit()

    def run_quality_suite(self, pipeline_run_id: Optional[int] = None) -> DataQualityRun:
        with log_duration("data_quality_run", pipeline_run_id=pipeline_run_id):
            active_datasets = get_active_datasets()

            # Initialize Run Record
            quality_run = DataQualityRun(
                pipeline_run_id=pipeline_run_id,
                status="PASS",
                started_at=datetime.now(timezone.utc),
                datasets_checked=len(active_datasets)
            )
            self.db.add(quality_run)
            self.db.commit()
            self.db.refresh(quality_run)

            passed = 0
            warned = 0
            failed = 0

            for target in active_datasets:
                key = target["dataset_key"]
                status = self.run_checks_for_dataset(quality_run.id, key)
                if status == "PASS":
                    passed += 1
                elif status == "WARNING":
                    warned += 1
                else:
                    failed += 1

            quality_run.checks_passed = passed
            quality_run.checks_warned = warned
            quality_run.checks_failed = failed

            # Aggregate Run Status
            if failed > 0:
                quality_run.status = "FAIL"
            elif warned > 0:
                quality_run.status = "WARNING"
            else:
                quality_run.status = "PASS"

            quality_run.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(quality_run)

            # Dispatch notification if data quality checks fail
            from app.notifications import NotificationDispatcher, NotificationEventType, NotificationSeverity
            if quality_run.status == "FAIL":
                NotificationDispatcher.dispatch_event(
                    db=self.db,
                    event_type=NotificationEventType.DATA_QUALITY_FAILURE,
                    severity=NotificationSeverity.SEVERE,
                    title="Data Quality Checks Failed",
                    message=f"Data quality run {quality_run.id} failed. Checks failed: {failed}, warned: {warned}.",
                    entity_type="DATA_QUALITY_RUN",
                    entity_id=quality_run.id
                )

            return quality_run

    @classmethod
    def check_dataset_gating(cls, db: Session, dataset_key: str) -> str:
        """
        Enforce quality gating rule. Retrieves latest status for the dataset.
        Returns: 'PASS', 'WARNING', or 'FAIL'. Defaults to 'PASS' if no checks exist.
        """
        # Fetch the latest check result for this dataset
        latest_res = db.query(DataQualityResult).filter(
            DataQualityResult.dataset_key == dataset_key
        ).order_by(DataQualityResult.id.desc()).first()
        
        if not latest_res:
            return "PASS"
        return latest_res.status
