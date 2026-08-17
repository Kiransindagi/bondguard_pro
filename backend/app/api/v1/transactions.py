
from app.auth.dependencies import PermissionChecker
from app.auth.permissions import PORTFOLIO_READ, PORTFOLIO_WRITE
from app.db.database import get_db
from app.db.models import Transaction
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.position import PositionService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("", response_model=TransactionResponse, dependencies=[Depends(PermissionChecker(PORTFOLIO_WRITE))])
def create_transaction(schema: TransactionCreate, db: Session = Depends(get_db)):
    svc = PositionService(db)
    try:
        return svc.execute_transaction(schema)
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=list[TransactionResponse], dependencies=[Depends(PermissionChecker(PORTFOLIO_READ))])
def list_transactions(portfolio_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Transaction)
    if portfolio_id is not None:
        query = query.filter(Transaction.portfolio_id == portfolio_id)
    return query.order_by(Transaction.trade_date.desc(), Transaction.id.desc()).all()

