
from app.auth.dependencies import PermissionChecker, get_current_user
from app.auth.permissions import PORTFOLIO_READ, PORTFOLIO_WRITE
from app.db.database import get_db
from app.db.models import Position, User
from app.schemas.portfolio import PortfolioCreate, PortfolioResponse, PortfolioUpdate
from app.schemas.position import PositionResponse
from app.services.portfolio import PortfolioService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("", response_model=PortfolioResponse, dependencies=[Depends(PermissionChecker(PORTFOLIO_WRITE))])
def create_portfolio(schema: PortfolioCreate, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    return svc.create_portfolio(schema)

@router.get("", response_model=list[PortfolioResponse])
def list_portfolios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _checker=Depends(PermissionChecker(PORTFOLIO_READ))
):
    svc = PortfolioService(db)
    is_admin = any(role.name == "ADMIN" for role in current_user.roles)
    return svc.list_portfolios(active_only=not is_admin)

@router.get("/{portfolio_id}", response_model=PortfolioResponse, dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    port = svc.get_portfolio(portfolio_id)
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return port

@router.patch("/{portfolio_id}", response_model=PortfolioResponse, dependencies=[Depends(PermissionChecker(PORTFOLIO_WRITE))])
def update_portfolio(portfolio_id: int, schema: PortfolioUpdate, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    port = svc.update_portfolio(portfolio_id, schema)
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return port

@router.delete("/{portfolio_id}", dependencies=[Depends(PermissionChecker(PORTFOLIO_WRITE))])
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    success = svc.delete_portfolio(portfolio_id)
    if not success:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {"status": "deleted"}

@router.get("/{portfolio_id}/positions", response_model=list[PositionResponse], dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])
def get_portfolio_positions(portfolio_id: int, db: Session = Depends(get_db)):
    return db.query(Position).filter(Position.portfolio_id == portfolio_id).all()

@router.get("/{portfolio_id}/summary", dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])
def get_portfolio_summary(portfolio_id: int, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    summary = svc.get_portfolio_summary(portfolio_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return summary

@router.post("/{portfolio_id}/reconcile", dependencies=[Depends(PermissionChecker(PORTFOLIO_WRITE))])
def reconcile_portfolio_positions(portfolio_id: int, db: Session = Depends(get_db)):
    svc = PortfolioService(db)
    port = svc.get_portfolio(portfolio_id)
    if not port:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    from app.services.position import PositionService
    pos_svc = PositionService(db)
    reconciled = pos_svc.reconcile_portfolio_positions(portfolio_id)
    return {"portfolio_id": portfolio_id, "reconciled": reconciled, "status": "success"}

