from sqlalchemy.orm import Session
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.db.models import Breach, RiskLimit, RiskEvaluationRun
from app.risk_control.enums import BreachStatus
from app.risk_control.audit_service import AuditService

class BreachManager:
    @staticmethod
    def handle_breach(
        db: Session, 
        portfolio_id: int, 
        limit: RiskLimit, 
        run: RiskEvaluationRun, 
        observed_value: Decimal, 
        threshold: Decimal, 
        breach_amount: Decimal
    ):
        existing = db.query(Breach).filter(
            Breach.portfolio_id == portfolio_id,
            Breach.risk_limit_id == limit.id,
            Breach.status.in_([BreachStatus.OPEN.value, BreachStatus.ACKNOWLEDGED.value])
        ).first()
        
        if existing:
            # Update existing unresolved breach
            prev_state = {
                "observed_value": float(existing.observed_value),
                "breach_amount": float(existing.breach_amount),
                "latest_evaluation_run_id": existing.latest_evaluation_run_id
            }
            existing.latest_evaluation_run_id = run.id
            existing.observed_value = observed_value
            existing.breach_amount = breach_amount
            
            new_state = {
                "observed_value": float(observed_value),
                "breach_amount": float(breach_amount),
                "latest_evaluation_run_id": run.id
            }
            AuditService.append_event(
                db, "BREACH_UPDATED", "BREACH", existing.id, "UPDATE",
                previous_state=prev_state, new_state=new_state
            )
        else:
            # Create new open breach
            new_breach = Breach(
                portfolio_id=portfolio_id,
                risk_limit_id=limit.id,
                first_evaluation_run_id=run.id,
                latest_evaluation_run_id=run.id,
                status=BreachStatus.OPEN.value,
                severity=limit.severity,
                observed_value=observed_value,
                threshold_value=threshold,
                breach_amount=breach_amount,
                opened_at=datetime.utcnow()
            )
            db.add(new_breach)
            db.flush()
            
            AuditService.append_event(
                db, "BREACH_OPENED", "BREACH", new_breach.id, "CREATE",
                new_state={
                    "status": BreachStatus.OPEN.value, 
                    "observed_value": float(observed_value), 
                    "threshold_value": float(threshold)
                }
            )

    @staticmethod
    def resolve_breach_if_any(
        db: Session, 
        portfolio_id: int, 
        limit: RiskLimit, 
        run: RiskEvaluationRun
    ):
        existing = db.query(Breach).filter(
            Breach.portfolio_id == portfolio_id,
            Breach.risk_limit_id == limit.id,
            Breach.status.in_([BreachStatus.OPEN.value, BreachStatus.ACKNOWLEDGED.value])
        ).first()
        
        if existing:
            prev_state = {"status": existing.status}
            existing.status = BreachStatus.RESOLVED.value
            existing.resolved_at = datetime.utcnow()
            existing.resolution_note = f"Automatically resolved by evaluation run {run.id}"
            
            new_state = {"status": BreachStatus.RESOLVED.value}
            AuditService.append_event(
                db, "BREACH_RESOLVED", "BREACH", existing.id, "UPDATE",
                previous_state=prev_state, new_state=new_state
            )
