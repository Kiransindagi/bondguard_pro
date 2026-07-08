from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import endpoints, market, portfolios, bonds, transactions, risk, market_risk, stress_testing, liquidity_risk, risk_control, reporting
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix=settings.API_V1_STR)
app.include_router(market.router, prefix=f"{settings.API_V1_STR}/market", tags=["market"])
app.include_router(portfolios.router, prefix=f"{settings.API_V1_STR}/portfolios", tags=["portfolios"])
app.include_router(bonds.router, prefix=f"{settings.API_V1_STR}/bonds", tags=["bonds"])
app.include_router(transactions.router, prefix=f"{settings.API_V1_STR}/transactions", tags=["transactions"])
app.include_router(risk.router, prefix=f"{settings.API_V1_STR}/risk", tags=["risk"])
app.include_router(market_risk.router, prefix=f"{settings.API_V1_STR}/market-risk", tags=["market_risk"])
app.include_router(stress_testing.router, prefix=f"{settings.API_V1_STR}", tags=["stress_testing"])
app.include_router(liquidity_risk.router, prefix=f"{settings.API_V1_STR}/liquidity-risk", tags=["liquidity_risk"])
app.include_router(risk_control.router, prefix=f"{settings.API_V1_STR}/risk-control", tags=["risk_control"])
app.include_router(reporting.router, prefix=f"{settings.API_V1_STR}/reporting", tags=["reporting"])

from app.risk_control import setup_risk_control
setup_risk_control()

@app.get("/")
def read_root():
    return {"message": "Welcome to BondGuard Pro API"}

@app.get("/health")
def read_health():
    return {"status": "ok"}
