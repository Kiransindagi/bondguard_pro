from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.db.database import get_db
from app.db.models import Portfolio, RiskEvaluationRun, Breach, AuditEvent, RiskLimitResult, RiskLimit
from app.risk_control.evaluator import LimitEvaluator
from app.risk_control.enums import BreachStatus
from app.risk_control.audit_service import AuditService
from app.schemas.risk_control import RiskLimitCreate, RiskLimitUpdate, RiskLimitResponse, RiskReportResponse
from app.risk_control.reporting_service import ReportingService

from app.auth.dependencies import PermissionChecker
from app.auth.permissions import RISK_READ, RISK_EXECUTE, BREACH_ACKNOWLEDGE, LIMIT_MANAGE, REPORT_GENERATE, AUDIT_READ, BREACH_READ, BREACH_ASSIGN, BREACH_REVIEW, BREACH_RESOLVE

router = APIRouter()

@router.post("/portfolios/{portfolio_id}/evaluate", dependencies=[Depends(PermissionChecker(RISK_EXECUTE))])
def evaluate_portfolio_limits(portfolio_id: int, valuation_date: date = None, db: Session = Depends(get_db)):
    if not valuation_date:
        valuation_date = date.today()
        
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    run = LimitEvaluator.evaluate_portfolio(db, portfolio_id, valuation_date)
    return {
        "id": run.id,
        "portfolio_id": run.portfolio_id,
        "valuation_date": run.valuation_date,
        "overall_status": run.overall_status,
        "evaluated_limit_count": run.evaluated_limit_count,
        "breach_count": run.breach_count,
        "warning_count": run.warning_count,
        "model_status": run.model_status,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "error_message": run.error_message
    }

@router.get("/portfolios/{portfolio_id}/latest", dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_latest_evaluation(portfolio_id: int, db: Session = Depends(get_db)):
    run = db.query(RiskEvaluationRun).filter(RiskEvaluationRun.portfolio_id == portfolio_id).order_by(RiskEvaluationRun.id.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="No evaluations found")
        
    results = db.query(RiskLimitResult).filter(RiskLimitResult.evaluation_run_id == run.id).all()
    
    return {
        "run": run,
        "results": results
    }

@router.get("/portfolios/{portfolio_id}/history", dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_evaluation_history(portfolio_id: int, limit: int = 10, db: Session = Depends(get_db)):
    runs = db.query(RiskEvaluationRun).filter(RiskEvaluationRun.portfolio_id == portfolio_id).order_by(RiskEvaluationRun.id.desc()).limit(limit).all()
    return runs

@router.get("/portfolios/{portfolio_id}/breaches", dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_active_breaches(portfolio_id: int, db: Session = Depends(get_db)):
    breaches = db.query(Breach).filter(
        Breach.portfolio_id == portfolio_id,
        Breach.status.in_([BreachStatus.OPEN.value, BreachStatus.ACKNOWLEDGED.value])
    ).all()
    return breaches

@router.get("/breaches/{breach_id}", dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_breach(breach_id: int, db: Session = Depends(get_db)):
    breach = db.query(Breach).filter(Breach.id == breach_id).first()
    if not breach:
        raise HTTPException(status_code=404, detail="Breach not found")
    return breach

@router.post("/breaches/{breach_id}/acknowledge", dependencies=[Depends(PermissionChecker(BREACH_ACKNOWLEDGE))])
def acknowledge_breach(breach_id: int, note: str = Query(None), db: Session = Depends(get_db)):
    breach = db.query(Breach).filter(Breach.id == breach_id).first()
    if not breach:
        raise HTTPException(status_code=404, detail="Breach not found")
        
    if breach.status != BreachStatus.OPEN.value:
        raise HTTPException(status_code=400, detail="Only OPEN breaches can be acknowledged")
        
    from datetime import datetime, timedelta
    prev_state = {"status": breach.status, "acknowledgement_note": breach.acknowledgement_note}
    
    breach.status = BreachStatus.ACKNOWLEDGED.value
    breach.acknowledgement_note = note
    breach.acknowledged_at = datetime.utcnow()
    # Set default SLA deadline: 2 days from now
    breach.sla_deadline = datetime.utcnow() + timedelta(days=2)
    
    AuditService.append_event(
        db, "BREACH_ACKNOWLEDGED", "BREACH", breach.id, "UPDATE",
        previous_state=prev_state,
        new_state={
            "status": breach.status,
            "acknowledgement_note": note,
            "sla_deadline": breach.sla_deadline.isoformat()
        }
    )
    
    db.commit()
    db.refresh(breach)

    # Dispatch notification
    from app.notifications import NotificationDispatcher, NotificationEventType, NotificationSeverity
    NotificationDispatcher.dispatch_event(
        db=db,
        event_type=NotificationEventType.BREACH_ACKNOWLEDGED,
        severity=NotificationSeverity.INFO,
        title="Breach Acknowledged",
        message=f"Breach for limit {breach.risk_limit_id} acknowledged by user. Note: {note}",
        entity_type="BREACH",
        entity_id=breach.id
    )

    return breach

@router.get("/audit-events", dependencies=[Depends(PermissionChecker(AUDIT_READ))])
def get_audit_events(entity_type: str = None, entity_id: int = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(AuditEvent)
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)
        
    return query.order_by(AuditEvent.id.desc()).limit(limit).all()

@router.get("/limits", response_model=List[RiskLimitResponse], dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_limits(db: Session = Depends(get_db)):
    from app.db.models import RiskLimit
    return db.query(RiskLimit).all()

@router.get("/limits/{limit_id}", response_model=RiskLimitResponse, dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_limit(limit_id: int, db: Session = Depends(get_db)):
    from app.db.models import RiskLimit
    limit = db.query(RiskLimit).filter(RiskLimit.id == limit_id).first()
    if not limit:
        raise HTTPException(status_code=404, detail="Limit not found")
    return limit

@router.post("/limits", response_model=RiskLimitResponse, dependencies=[Depends(PermissionChecker(LIMIT_MANAGE))])
def create_limit(limit_in: RiskLimitCreate, db: Session = Depends(get_db)):
    from app.db.models import RiskLimit
    from app.risk_control.reporting_service import ReportingService  # noqa: F401
    existing = db.query(RiskLimit).filter(
        RiskLimit.metric_type == limit_in.metric_type,
        RiskLimit.scope_type == limit_in.scope_type,
        RiskLimit.scope_value == limit_in.scope_value,
        RiskLimit.is_active.is_(True)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Duplicate active limit for this metric and scope exists")
        
    db_limit = RiskLimit(**limit_in.dict(), is_active=True)
    db.add(db_limit)
    db.commit()
    db.refresh(db_limit)
    
    AuditService.append_event(
        db, "LIMIT_CREATED", "RISK_LIMIT", db_limit.id, "CREATE",
        new_state={"code": db_limit.code, "metric": db_limit.metric_type, "limit_threshold": float(db_limit.limit_threshold)}
    )
    db.commit()
    return db_limit

@router.patch("/limits/{limit_id}", response_model=RiskLimitResponse, dependencies=[Depends(PermissionChecker(LIMIT_MANAGE))])
def update_limit(limit_id: int, limit_update: RiskLimitUpdate, db: Session = Depends(get_db)):
    db_limit = db.query(RiskLimit).filter(RiskLimit.id == limit_id).first()
    if not db_limit:
        raise HTTPException(status_code=404, detail="Limit not found")
        
    prev_state = {"limit_threshold": float(db_limit.limit_threshold)}
    
    update_data = limit_update.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(db_limit, k, v)
        
    AuditService.append_event(
        db, "LIMIT_UPDATED", "RISK_LIMIT", db_limit.id, "UPDATE",
        previous_state=prev_state,
        new_state={"limit_threshold": float(db_limit.limit_threshold)}
    )
    db.commit()
    db.refresh(db_limit)
    return db_limit

@router.delete("/limits/{limit_id}", dependencies=[Depends(PermissionChecker(LIMIT_MANAGE))])
def delete_limit(limit_id: int, db: Session = Depends(get_db)):
    db_limit = db.query(RiskLimit).filter(RiskLimit.id == limit_id).first()
    if not db_limit:
        raise HTTPException(status_code=404, detail="Limit not found")
        
    db_limit.is_active = False
    
    AuditService.append_event(
        db, "LIMIT_DEACTIVATED", "RISK_LIMIT", db_limit.id, "UPDATE",
        previous_state={"is_active": True},
        new_state={"is_active": False}
    )
    db.commit()
    return {"message": "Limit deactivated"}

@router.get("/portfolios/{portfolio_id}/report", response_model=RiskReportResponse, dependencies=[Depends(PermissionChecker(REPORT_GENERATE))])
def get_portfolio_risk_report(portfolio_id: int, db: Session = Depends(get_db)):
    try:
        report = ReportingService.generate_report(db, portfolio_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/breaches/{breach_id}/workflow", dependencies=[Depends(PermissionChecker(BREACH_READ))])
def get_breach_workflow_details(breach_id: int, db: Session = Depends(get_db)):
    breach = db.query(Breach).filter(Breach.id == breach_id).first()
    if not breach:
        raise HTTPException(status_code=404, detail="Breach not found")
    
    history = db.query(AuditEvent).filter(
        AuditEvent.entity_type == "BREACH",
        AuditEvent.entity_id == breach_id
    ).order_by(AuditEvent.id.asc()).all()
    
    from datetime import datetime, timezone
    is_overdue = False
    if breach.status in ["OPEN", "ACKNOWLEDGED", "UNDER_REVIEW"] and breach.sla_deadline:
        now = datetime.now(timezone.utc)
        deadline = breach.sla_deadline
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        is_overdue = now > deadline

    return {
        "breach": breach,
        "history": history,
        "is_overdue": is_overdue
    }


@router.post("/breaches/{breach_id}/assign", dependencies=[Depends(PermissionChecker(BREACH_ASSIGN))])
def assign_breach(breach_id: int, user_id: int, db: Session = Depends(get_db)):
    breach = db.query(Breach).filter(Breach.id == breach_id).first()
    if not breach:
        raise HTTPException(status_code=404, detail="Breach not found")
        
    from app.db.models import User
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Assigned user not found")
        
    prev_state = {"assigned_user_id": breach.assigned_user_id, "assigned_to": breach.assigned_to}
    
    breach.assigned_user_id = user.id
    breach.assigned_to = user.username
    
    AuditService.append_event(
        db, "BREACH_ASSIGNED", "BREACH", breach.id, "UPDATE",
        previous_state=prev_state,
        new_state={"assigned_user_id": user.id, "assigned_to": user.username}
    )
    db.commit()
    db.refresh(breach)
    return breach


@router.post("/breaches/{breach_id}/review", dependencies=[Depends(PermissionChecker(BREACH_REVIEW))])
def review_breach(breach_id: int, notes: str = Query(None), db: Session = Depends(get_db)):
    breach = db.query(Breach).filter(Breach.id == breach_id).first()
    if not breach:
        raise HTTPException(status_code=404, detail="Breach not found")
        
    prev_state = {"status": breach.status, "review_notes": breach.review_notes}
    
    from datetime import datetime
    breach.status = "UNDER_REVIEW"
    breach.under_review_at = datetime.utcnow()
    breach.review_notes = notes
    
    AuditService.append_event(
        db, "BREACH_UNDER_REVIEW", "BREACH", breach.id, "UPDATE",
        previous_state=prev_state,
        new_state={"status": breach.status, "review_notes": notes}
    )
    db.commit()
    db.refresh(breach)
    return breach


@router.post("/breaches/{breach_id}/resolve", dependencies=[Depends(PermissionChecker(BREACH_RESOLVE))])
def resolve_breach(breach_id: int, notes: str = Query(None), db: Session = Depends(get_db)):
    breach = db.query(Breach).filter(Breach.id == breach_id).first()
    if not breach:
        raise HTTPException(status_code=404, detail="Breach not found")
        
    prev_state = {"status": breach.status, "resolution_note": breach.resolution_note}
    
    from datetime import datetime
    breach.status = BreachStatus.RESOLVED.value
    breach.resolved_at = datetime.utcnow()
    breach.resolution_note = notes
    
    AuditService.append_event(
        db, "BREACH_RESOLVED", "BREACH", breach.id, "UPDATE",
        previous_state=prev_state,
        new_state={"status": breach.status, "resolution_note": notes}
    )
    db.commit()
    db.refresh(breach)
    
    # Dispatch resolved notification
    from app.notifications import NotificationDispatcher, NotificationEventType, NotificationSeverity
    NotificationDispatcher.dispatch_event(
        db=db,
        event_type=NotificationEventType.BREACH_RESOLVED,
        severity=NotificationSeverity.INFO,
        title="Breach Resolved",
        message=f"Breach for limit {breach.risk_limit_id} resolved by user. Note: {notes}",
        entity_type="BREACH",
        entity_id=breach.id
    )
    
    return breach


@router.get("/assignable-users", dependencies=[Depends(PermissionChecker(BREACH_READ))])
def get_assignable_users(db: Session = Depends(get_db)):
    from app.db.models import User
    users = db.query(User).filter(User.is_active.is_(True)).all()
    return [{"id": u.id, "username": u.username, "roles": [r.name for r in u.roles]} for u in users]
