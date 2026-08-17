from enum import Enum

from pydantic import BaseModel


class LiquidityClass(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"

class HorizonBucket(str, Enum):
    ONE_DAY = "1_DAY"
    TWO_TO_FIVE_DAYS = "2_TO_5_DAYS"
    SIX_TO_TEN_DAYS = "6_TO_10_DAYS"
    ELEVEN_TO_TWENTY_DAYS = "11_TO_20_DAYS"
    OVER_TWENTY_DAYS = "OVER_20_DAYS"

class LimitStatus(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    BREACH = "BREACH"

class StressScenarioType(str, Enum):
    NORMAL = "NORMAL"
    MODERATE = "MODERATE"
    SEVERE = "SEVERE"
    CREDIT_MARKET_FREEZE = "CREDIT_MARKET_FREEZE"

class LiquidityAssumptionConfig(BaseModel):
    version: str
    base_spread_bps_treasury: float = 1.0
    base_spread_bps_ig: float = 10.0
    base_spread_bps_hy: float = 50.0
    base_spread_bps_em: float = 100.0

    base_capacity_treasury: float = 100000000.0
    base_capacity_ig: float = 10000000.0
    base_capacity_hy: float = 1000000.0
    base_capacity_em: float = 500000.0

    participation_rate_normal: float = 0.20
    participation_rate_conservative: float = 0.10
    participation_rate_stressed: float = 0.05
    
    # Weights for score
    weight_type: float = 0.4
    weight_rating: float = 0.3
    weight_maturity: float = 0.15
    weight_concentration: float = 0.15
