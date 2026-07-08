from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.db.database import get_db
from app.db.models import Portfolio, RiskEvaluationRun, Breach, AuditEvent, RiskLimitResult
from app.risk_control.evaluator import LimitEvaluator
from app.risk_control.enums import BreachStatus
from app.risk_control.audit_service import AuditService

router = APIRouter()

@router.post("/portfolios/{portfolio_id}/evaluate")
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

@router.get("/portfolios/{portfolio_id}/latest")
def get_latest_evaluation(portfolio_id: int, db: Session = Depends(get_db)):
    run = db.query(RiskEvaluationRun).filter(RiskEvaluationRun.portfolio_id == portfolio_id).order_by(RiskEvaluationRun.id.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="No evaluations found")
        
    results = db.query(RiskLimitResult).filter(RiskLimitResult.evaluation_run_id == run.id).all()
    
    return {
        "run": run,
        "results": results
    }

@router.get("/portfolios/{portfolio_id}/history")
def get_evaluation_history(portfolio_id: int, limit: int = 10, db: Session = Depends(get_db)):
    runs = db.query(RiskEvaluationRun).filter(RiskEvaluationRun.portfolio_id == portfolio_id).order_by(RiskEvaluationRun.id.desc()).limit(limit).all()
    return runs

@router.get("/portfolios/{portfolio_id}/breaches")
def get_active_breaches(portfolio_id: int, db: Session = Depends(get_db)):
    breaches = db.query(Breach).filter(
        Breach.portfolio_id == portfolio_id,
        Breach.status.in_([BreachStatus.OPEN.value, BreachStatus.ACKNOWLEDGED.value])
    ).all()
    return breaches

@router.get("/breaches/{breach_id}")
def get_breach(breach_id: int, db: Session = Depends(get_db)):
    breach = db.query(Breach).filter(Breach.id == breach_id).first()
    if not breach:
        raise HTTPException(status_code=404, detail="Breach not found")
    return breach

@router.post("/breaches/{breach_id}/acknowledge")
def acknowledge_breach(breach_id: int, note: str = Query(None), db: Session = Depends(get_db)):
    breach = db.query(Breach).filter(Breach.id == breach_id).first()
    if not breach:
        raise HTTPException(status_code=404, detail="Breach not found")
        
    if breach.status != BreachStatus.OPEN.value:
        raise HTTPException(status_code=400, detail="Only OPEN breaches can be acknowledged")
        
    from datetime import datetime
    prev_state = {"status": breach.status, "acknowledgement_note": breach.acknowledgement_note}
    
    breach.status = BreachStatus.ACKNOWLEDGED.value
    breach.acknowledgement_note = note
    breach.acknowledged_at = datetime.utcnow()
    
    AuditService.append_event(
        db, "BREACH_ACKNOWLEDGED", "BREACH", breach.id, "UPDATE",
        previous_state=prev_state,
        new_state={"status": breach.status, "acknowledgement_note": note}
    )
    
    db.commit()
    db.refresh(breach)
    return breach

@router.get("/audit-events")
def get_audit_events(entity_type: str = None, entity_id: int = None, limit: int = 50, db: Session = Depends(get_db)):
    query = db.query(AuditEvent)
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)
        
    return query.order_by(AuditEvent.id.desc()).limit(limit).all()
from app.schemas.risk_control import RiskLimitCreate, RiskLimitUpdate, RiskLimitResponse, RiskReportResponse
from app.db.models import RiskLimit
from app.risk_control.reporting_service import ReportingService

@router.get("/limits", response_model=List[RiskLimitResponse])
def get_limits(db: Session = Depends(get_db)):
    return db.query(RiskLimit).all()

@router.get("/limits/{limit_id}", response_model=RiskLimitResponse)
def get_limit(limit_id: int, db: Session = Depends(get_db)):
    limit = db.query(RiskLimit).filter(RiskLimit.id == limit_id).first()
    if not limit:
        raise HTTPException(status_code=404, detail="Limit not found")
    return limit

@router.post("/limits", response_model=RiskLimitResponse)
def create_limit(limit_in: RiskLimitCreate, db: Session = Depends(get_db)):
    existing = db.query(RiskLimit).filter(
        RiskLimit.metric_type == limit_in.metric_type,
        RiskLimit.scope_type == limit_in.scope_type,
        RiskLimit.scope_value == limit_in.scope_value,
        RiskLimit.is_active == True
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

@router.patch("/limits/{limit_id}", response_model=RiskLimitResponse)
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

@router.delete("/limits/{limit_id}")
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

@router.get("/portfolios/{portfolio_id}/report", response_model=RiskReportResponse)
def get_portfolio_risk_report(portfolio_id: int, db: Session = Depends(get_db)):
    try:
        report = ReportingService.generate_report(db, portfolio_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
