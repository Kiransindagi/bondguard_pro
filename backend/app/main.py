from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import endpoints, market, portfolios, bonds, transactions, risk, market_risk, stress_testing, liquidity_risk, risk_control, reporting, data_pipeline, data_quality, analytics, auth, admin, notifications, scenario_lab, advanced_risk
from app.core.observability import CorrelationIdMiddleware, setup_structured_logging
import logging

setup_structured_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Custom Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    # Relaxed slightly to allow Swagger UI scripts/styles to load correctly
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data:;"
    )
    return response

app.add_middleware(CorrelationIdMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
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
app.include_router(data_pipeline.router, prefix=f"{settings.API_V1_STR}/data-pipeline", tags=["data_pipeline"])
app.include_router(data_quality.router, prefix=f"{settings.API_V1_STR}/data-quality", tags=["data_quality"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])
app.include_router(notifications.router, prefix=f"{settings.API_V1_STR}/notifications", tags=["notifications"])
app.include_router(scenario_lab.router, prefix=f"{settings.API_V1_STR}/scenario-lab", tags=["scenario_lab"])
app.include_router(advanced_risk.router, prefix=f"{settings.API_V1_STR}/advanced-risk", tags=["advanced_risk"])

from app.risk_control import setup_risk_control  # noqa: E402
setup_risk_control()

@app.get("/")
def read_root():
    return {"message": "Welcome to BondGuard Pro API"}

@app.get("/health")
def read_health():
    return {"status": "ok"}

