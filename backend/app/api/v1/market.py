from datetime import date

from app.auth.dependencies import PermissionChecker
from app.auth.permissions import PORTFOLIO_READ
from app.db.database import get_db
from app.db.models import (
    CreditSpread,
    DataIngestionRun,
    Instrument,
    MacroObservation,
    MarketPrice,
    YieldCurvePoint,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

router = APIRouter(dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])

@router.get("/yield-curve")
def get_yield_curve(date: date | None = None, db: Session = Depends(get_db)):
    if not date:
        latest_point = db.query(YieldCurvePoint).order_by(desc(YieldCurvePoint.observation_date)).first()
        if not latest_point:
            return []
        date = latest_point.observation_date

    points = db.query(YieldCurvePoint).filter(YieldCurvePoint.observation_date == date).all()
    return [{"observation_date": p.observation_date, "tenor_years": p.tenor_years, "yield_percent": p.yield_percent} for p in points]

@router.get("/prices")
def get_prices(symbol: str, start_date: date | None = None, end_date: date | None = None, db: Session = Depends(get_db)):
    inst = db.query(Instrument).filter(Instrument.symbol == symbol).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Instrument not found")

    query = db.query(MarketPrice).filter(MarketPrice.instrument_id == inst.id)
    if start_date:
        query = query.filter(MarketPrice.observation_date >= start_date)
    if end_date:
        query = query.filter(MarketPrice.observation_date <= end_date)

    prices = query.order_by(MarketPrice.observation_date).all()
    return [{
        "observation_date": p.observation_date,
        "open": p.open,
        "high": p.high,
        "low": p.low,
        "close": p.close,
        "adjusted_close": p.adjusted_close,
        "volume": p.volume,
        "source": p.source
    } for p in prices]

@router.get("/spreads")
def get_spreads(spread_type: str | None = None, start_date: date | None = None, end_date: date | None = None, db: Session = Depends(get_db)):
    query = db.query(CreditSpread)
    if spread_type:
        query = query.filter(CreditSpread.spread_type == spread_type)
    if start_date:
        query = query.filter(CreditSpread.observation_date >= start_date)
    if end_date:
        query = query.filter(CreditSpread.observation_date <= end_date)

    spreads = query.order_by(desc(CreditSpread.observation_date)).limit(100).all() # limit to avoid huge payload
    return [{
        "observation_date": s.observation_date,
        "spread_type": s.spread_type,
        "spread_bps": s.spread_bps
    } for s in spreads]

@router.get("/macro")
def get_macro(metric: str | None = None, start_date: date | None = None, end_date: date | None = None, db: Session = Depends(get_db)):
    query = db.query(MacroObservation)
    if metric:
        query = query.filter(MacroObservation.metric_name == metric)
    if start_date:
        query = query.filter(MacroObservation.observation_date >= start_date)
    if end_date:
        query = query.filter(MacroObservation.observation_date <= end_date)

    obs = query.order_by(desc(MacroObservation.observation_date)).limit(100).all()
    return [{
        "observation_date": o.observation_date,
        "metric_name": o.metric_name,
        "value": o.value
    } for o in obs]

@router.get("/data-status")
def get_data_status(db: Session = Depends(get_db)):
    datasets = db.query(DataIngestionRun.dataset).distinct().all()
    status_list = []
    
    for (dataset,) in datasets:
        latest_run = db.query(DataIngestionRun).filter(DataIngestionRun.dataset == dataset).order_by(desc(DataIngestionRun.started_at)).first()
        if latest_run:
            status_list.append({
                "source": latest_run.source,
                "dataset": latest_run.dataset,
                "last_successful_update": latest_run.completed_at if latest_run.status == "SUCCESS" else None,
                "last_status": latest_run.status,
                "records_fetched": latest_run.records_fetched,
                "records_inserted": latest_run.records_inserted,
            })
            
    return status_list
