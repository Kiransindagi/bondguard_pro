from datetime import datetime
from decimal import Decimal

from app.db.models import RiskEvaluationRun, RiskLimitResult
from app.risk_control.audit_service import AuditService
from app.risk_control.breach_manager import BreachManager
from app.risk_control.enums import (
    EvaluationOverallStatus,
    LimitDirection,
    MetricType,
    ResultStatus,
)
from app.risk_control.limit_resolver import LimitResolver
from app.risk_control.metric_registry import registry
from sqlalchemy.orm import Session


class LimitEvaluator:
    @staticmethod
    def _evaluate_threshold(value: Decimal, limit) -> ResultStatus:
        threshold = Decimal(str(limit.limit_threshold))
        warn_threshold = Decimal(str(limit.warning_threshold)) if limit.warning_threshold is not None else None
        
        if limit.direction == LimitDirection.MAXIMUM.value:
            if value > threshold:
                return ResultStatus.BREACH
            if warn_threshold is not None and value >= warn_threshold:
                return ResultStatus.WARNING
            return ResultStatus.PASS
        else: # MINIMUM
            if value < threshold:
                return ResultStatus.BREACH
            if warn_threshold is not None and value <= warn_threshold:
                return ResultStatus.WARNING
            return ResultStatus.PASS

    @staticmethod
    def evaluate_portfolio(db: Session, portfolio_id: int, valuation_date: datetime.date) -> RiskEvaluationRun:
        try:
            # 1. Resolve limits
            limits = LimitResolver.resolve_applicable_limits(db, portfolio_id, valuation_date)
            
            started_at = datetime.utcnow()
            run = RiskEvaluationRun(
                portfolio_id=portfolio_id,
                valuation_date=valuation_date,
                model_status="FULL", # Temp, will aggregate
                started_at=started_at,
                completed_at=started_at,
                overall_status=EvaluationOverallStatus.PASS.value,
                evaluated_limit_count=0,
                breach_count=0,
                warning_count=0
            )
            db.add(run)
            db.flush()
            
            eval_count = 0
            breach_count = 0
            warning_count = 0
            overall_status = EvaluationOverallStatus.PASS
            model_statuses = set()
            
            for limit in limits:
                metric = MetricType(limit.metric_type)
                adapter = registry.get_adapter(metric)
                if not adapter:
                    # explicit controlled error or NOT_EVALUATED
                    res_status = ResultStatus.NOT_EVALUATED
                    value = None
                    threshold = Decimal(str(limit.limit_threshold))
                    utilization = None
                    breach_amount = None
                    unit = "N/A"
                    source = "UNKNOWN_ADAPTER"
                else:
                    norm_result = adapter.get_value(metric, portfolio_id, valuation_date, db)
                    
                    if norm_result.value is None or norm_result.model_status in ("UNAVAILABLE", "ERROR"):
                        res_status = ResultStatus.NOT_EVALUATED
                        value = None
                        threshold = Decimal(str(limit.limit_threshold))
                        utilization = None
                        breach_amount = None
                        unit = norm_result.unit
                        source = norm_result.calculation_source
                        if norm_result.model_status:
                            model_statuses.add(norm_result.model_status)
                    else:
                        value = norm_result.value
                        threshold = Decimal(str(limit.limit_threshold))
                        res_status = LimitEvaluator._evaluate_threshold(value, limit)
                        unit = norm_result.unit
                        source = norm_result.calculation_source
                        if norm_result.model_status:
                            model_statuses.add(norm_result.model_status)
                            
                        # calculate utilization and breach amount using Decimal semantics
                        if threshold == Decimal(0):
                            utilization = 1.0 if value > 0 else 0.0
                        else:
                            utilization = float(value / threshold)
                            
                        if res_status == ResultStatus.BREACH:
                            breach_amount = value - threshold if limit.direction == LimitDirection.MAXIMUM.value else threshold - value
                        else:
                            breach_amount = None
                            
                # create result
                res = RiskLimitResult(
                    evaluation_run_id=run.id,
                    risk_limit_id=limit.id,
                    observed_value=value,
                    threshold_value=threshold,
                    utilization_percent=utilization,
                    result_status=res_status.value,
                    breach_amount=breach_amount,
                    metric_unit=unit,
                    calculation_source=source
                )
                db.add(res)
                eval_count += 1
                
                if res_status == ResultStatus.BREACH:
                    breach_count += 1
                    if overall_status != EvaluationOverallStatus.FAILED:
                        overall_status = EvaluationOverallStatus.BREACH
                    BreachManager.handle_breach(db, portfolio_id, limit, run, value, threshold, breach_amount)
                elif res_status == ResultStatus.WARNING:
                    warning_count += 1
                    if overall_status == EvaluationOverallStatus.PASS:
                        overall_status = EvaluationOverallStatus.WARNING
                elif res_status == ResultStatus.PASS:
                    BreachManager.resolve_breach_if_any(db, portfolio_id, limit, run)

            run.completed_at = datetime.utcnow()
            run.evaluated_limit_count = eval_count
            run.breach_count = breach_count
            run.warning_count = warning_count
            run.overall_status = overall_status.value
            
            # Combine model statuses
            if "ERROR" in model_statuses:
                run.model_status = "ERROR"
            elif "CHARACTERISTIC_BASED_PROXY_V1" in model_statuses or "RATE_ONLY_MODEL" in model_statuses:
                run.model_status = "DEGRADED"
            elif not model_statuses:
                run.model_status = "NO_DATA"
            else:
                run.model_status = "AVAILABLE"
                
            AuditService.append_event(
                db, "EVALUATION_COMPLETED", "EVALUATION_RUN", run.id, "CREATE",
                new_state={"overall_status": run.overall_status, "breaches": breach_count, "warnings": warning_count}
            )
            db.commit()
            db.refresh(run)
            return run
        except Exception as e:
            db.rollback()
            # Try to save a failed run
            try:
                started_at = datetime.utcnow()
                failed_run = RiskEvaluationRun(
                    portfolio_id=portfolio_id,
                    valuation_date=valuation_date,
                    model_status="ERROR",
                    started_at=started_at,
                    completed_at=started_at,
                    overall_status=EvaluationOverallStatus.FAILED.value,
                    evaluated_limit_count=0,
                    breach_count=0,
                    warning_count=0,
                    error_message=str(e)[:250]
                )
                db.add(failed_run)
                db.commit()
                db.refresh(failed_run)
                return failed_run
            except Exception:
                db.rollback()
                raise
