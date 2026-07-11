from enum import Enum
from pydantic import BaseModel
from typing import Optional

class NotificationEventType(str, Enum):
    LIMIT_BREACH = "LIMIT_BREACH"
    SEVERE_BREACH = "SEVERE_BREACH"
    BREACH_ACKNOWLEDGED = "BREACH_ACKNOWLEDGED"
    BREACH_RESOLVED = "BREACH_RESOLVED"
    PIPELINE_FAILURE = "PIPELINE_FAILURE"
    PIPELINE_PARTIAL_SUCCESS = "PIPELINE_PARTIAL_SUCCESS"
    DATA_QUALITY_FAILURE = "DATA_QUALITY_FAILURE"
    RATE_MODEL_UNAVAILABLE = "RATE_MODEL_UNAVAILABLE"
    MODEL_DEGRADATION = "MODEL_DEGRADATION"
    ANALYTICS_FAILURE = "ANALYTICS_FAILURE"
    SEVERE_STRESS_LOSS = "SEVERE_STRESS_LOSS"
    LIQUIDITY_DETERIORATION = "LIQUIDITY_DETERIORATION"

class NotificationSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    SEVERE = "SEVERE"

class NotificationCreate(BaseModel):
    user_id: int
    event_type: NotificationEventType
    severity: NotificationSeverity
    title: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
