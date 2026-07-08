from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse
from app.services.position import PositionService

router = APIRouter()

@router.post("", response_model=TransactionResponse)
def create_transaction(schema: TransactionCreate, db: Session = Depends(get_db)):
    svc = PositionService(db)
    try:
        return svc.execute_transaction(schema)
    except Exception as e:
        db.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=str(e))
