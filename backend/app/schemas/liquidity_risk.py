from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from app.risk_engine.liquidity_risk.types import LiquidityClass, HorizonBucket, LimitStatus, StressScenarioType

class LiquidityAssumptionCreate(BaseModel):
    name: str
    version: str
    description: Optional[str] = None
    methodology: str
    configuration_json: Dict[str, Any]
    is_active: bool = True

class LiquidityAssumptionResponse(LiquidityAssumptionCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PositionLiquidityResponse(BaseModel):
    position_id: int
    bond_id: int
    bond_name: str
    issuer: str
    rating: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    maturity_date: date
    market_value: float

    liquidity_score: float
    liquidity_class: LiquidityClass

    estimated_bid_ask_bps: float
    estimated_liquidation_cost: float

    model_daily_capacity: float
    participation_rate: float

    raw_days_to_liquidate: float
    estimated_trading_days_to_liquidate: int
    liquidation_horizon_bucket: HorizonBucket

    source_type: str
    methodology: str
    assumption_version: str

    limitations: str

    class Config:
        from_attributes = True

class HorizonDistribution(BaseModel):
    bucket: HorizonBucket
    market_value: float
    percentage: float

class PortfolioLiquidityResponse(BaseModel):
    portfolio_id: int
    portfolio_name: str
    valuation_date: date

    portfolio_market_value: float

    weighted_liquidity_score: float

    estimated_total_liquidation_cost: float
    estimated_total_liquidation_cost_bps: float

    weighted_days_to_liquidate: float
    maximum_days_to_liquidate: int

    high_liquidity_weight: float
    medium_liquidity_weight: float
    low_liquidity_weight: float
    very_low_liquidity_weight: float

    largest_illiquid_position: Optional[str] = None

    liquidation_horizon_distribution: List[HorizonDistribution]

    methodology: str
    assumption_version: str
    limitations: str

    class Config:
        from_attributes = True

class LiquiditySnapshotResponse(PortfolioLiquidityResponse):
    id: int
    created_at: datetime
    
class LiquidityStressRequest(BaseModel):
    scenario: StressScenarioType
    assumption_id: Optional[int] = None

class LiquidityStressResponse(BaseModel):
    scenario: StressScenarioType
    normal_liquidation_cost: float
    stressed_liquidation_cost: float
    incremental_liquidity_cost: float
    normal_days_to_liquidate: float
    stressed_days_to_liquidate: float

class ConcentrationBreakdownItem(BaseModel):
    name: str
    market_value: float
    portfolio_weight: float
    position_count: int
    rank: int

class ConcentrationSummaryResponse(BaseModel):
    dimension: str
    breakdown: List[ConcentrationBreakdownItem]
    hhi: float
    hhi_scaled: float
    top_1_weight: float
    top_3_weight: float
    top_5_weight: float

class ConcentrationLimitCreate(BaseModel):
    portfolio_id: Optional[int] = None
    limit_type: str
    threshold_value: float
    warning_threshold_value: float
    is_active: bool = True

class ConcentrationLimitUpdate(BaseModel):
    threshold_value: Optional[float] = None
    warning_threshold_value: Optional[float] = None
    is_active: Optional[bool] = None

class ConcentrationLimitResponse(ConcentrationLimitCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LimitUtilizationResponse(BaseModel):
    limit: ConcentrationLimitResponse
    actual_value: float
    utilization_percent: float
    status: LimitStatus

class LiquidityAdjustedVaRResponse(BaseModel):
    market_var: float
    liquidity_cost_adjustment: float
    liquidity_adjusted_var: float
    confidence_level: float
    horizon_days: int
    market_risk_model_status: str
    liquidity_methodology: str
    limitations: str
