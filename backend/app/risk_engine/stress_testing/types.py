from enum import Enum
from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class CalculationMethod(str, Enum):
    FULL_REVALUATION = "FULL_REVALUATION"
    APPROXIMATION = "APPROXIMATION"

class ScenarioType(str, Enum):
    PARALLEL_RATE = "PARALLEL_RATE"
    NON_PARALLEL_RATE = "NON_PARALLEL_RATE"
    CREDIT_SPREAD = "CREDIT_SPREAD"
    COMBINED = "COMBINED"
    CUSTOM = "CUSTOM"

class StressScenarioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    scenario_type: ScenarioType
    is_predefined: bool = False
    rate_2y_shock_bps: float = 0.0
    rate_5y_shock_bps: float = 0.0
    rate_10y_shock_bps: float = 0.0
    rate_30y_shock_bps: float = 0.0
    ig_spread_shock_bps: float = 0.0
    hy_spread_shock_bps: float = 0.0
    default_calculation_method: CalculationMethod = CalculationMethod.FULL_REVALUATION

class StressScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rate_2y_shock_bps: Optional[float] = None
    rate_5y_shock_bps: Optional[float] = None
    rate_10y_shock_bps: Optional[float] = None
    rate_30y_shock_bps: Optional[float] = None
    ig_spread_shock_bps: Optional[float] = None
    hy_spread_shock_bps: Optional[float] = None
    default_calculation_method: Optional[CalculationMethod] = None

class StressScenarioResponse(StressScenarioCreate):
    id: int

class StressRunRequest(BaseModel):
    scenario_id: int
    calculation_method: Optional[CalculationMethod] = None

class StressPositionResultResponse(BaseModel):
    id: int
    bond_id: int
    bond_name: str
    issuer: str
    rating: str
    sector: str
    base_clean_price: float
    stressed_clean_price: float
    base_market_value: float
    stressed_market_value: float
    rate_shock_bps: float
    spread_shock_bps: float
    pnl: float
    pnl_percent: float
    contribution_percent: float

class StressRunResponse(BaseModel):
    id: int
    portfolio_id: int
    scenario_id: int
    valuation_date: date
    calculation_method: CalculationMethod
    base_market_value: float
    stressed_market_value: float
    total_pnl: float
    total_loss_percent: float
    position_count: int
    positions: List[StressPositionResultResponse] = []

class StressComparisonRequest(BaseModel):
    scenario_ids: List[int]

class PortfolioStressSummaryResponse(BaseModel):
    portfolio_id: int
    scenario_id: int
    scenario_name: str
    valuation_date: date
    calculation_method: CalculationMethod
    base_market_value: float
    stressed_market_value: float
    total_pnl: float
    total_loss_percent: float
    largest_loss_position_bond_id: Optional[int]
    largest_gain_position_bond_id: Optional[int]
    position_count: int
    rate_scenario_description: str
    credit_scenario_description: str
    limitations: Optional[str] = None

class StressComparisonResponse(BaseModel):
    portfolio_id: int
    valuation_date: date
    scenarios: List[PortfolioStressSummaryResponse]
