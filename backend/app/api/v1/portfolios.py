from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.portfolio import PortfolioCreate, PortfolioUpdate, PortfolioResponse
from app.schemas.position import PositionResponse
from app.services.portfolio import PortfolioService
from app.db.models import Position

router = APIRouter()

@router.post("", response_model=PortfolioResponse)
def create_portfolio(schema: PortfolioCreate, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    return svc.create_portfolio(schema)

@router.get("", response_model=List[PortfolioResponse])
def list_portfolios(db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    return svc.list_portfolios()

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    port = svc.get_portfolio(portfolio_id)
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return port

@router.patch("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(portfolio_id: int, schema: PortfolioUpdate, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    port = svc.update_portfolio(portfolio_id, schema)
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return port

@router.delete("/{portfolio_id}")
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    success = svc.delete_portfolio(portfolio_id)
    if not success:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {"status": "deleted"}

@router.get("/{portfolio_id}/positions", response_model=List[PositionResponse])
def get_portfolio_positions(portfolio_id: int, db: Session = Depends(get_db)):
    return db.query(Position).filter(Position.portfolio_id == portfolio_id).all()

@router.get("/{portfolio_id}/summary")
def get_portfolio_summary(portfolio_id: int, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    summary = svc.get_portfolio_summary(portfolio_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return summary
