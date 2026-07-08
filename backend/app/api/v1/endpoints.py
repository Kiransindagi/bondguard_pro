from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from pydantic import BaseModel

from app.db.database import get_db
from app.core.config import settings
from app.api.v1 import portfolios, bonds, transactions, market, risk, market_risk, stress_testing, liquidity_risk

router = APIRouter()

api_router = APIRouter()
api_router.include_router(portfolios.router, prefix="/portfolios", tags=["portfolios"])
api_router.include_router(bonds.router, prefix="/bonds", tags=["bonds"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(market_risk.router, prefix="/market-risk", tags=["market-risk"])
api_router.include_router(stress_testing.router, prefix="/stress-tests", tags=["stress-testing"])
api_router.include_router(liquidity_risk.router, prefix="/liquidity-risk", tags=["liquidity-risk"])

class StatusResponse(BaseModel):
    status: str
    environment: str
    version: str
    timestamp: str

class DatabaseStatusResponse(BaseModel):
    status: str
    timestamp: str

@router.get("/status", response_model=StatusResponse)
def get_status():
    return StatusResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@router.get("/system/database", response_model=DatabaseStatusResponse)
def get_database_status(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return DatabaseStatusResponse(
            status="connected",
            timestamp=datetime.now(timezone.utc).isoformat()
        )
    except Exception:
        raise HTTPException(status_code=503, detail="Database connection failed")
