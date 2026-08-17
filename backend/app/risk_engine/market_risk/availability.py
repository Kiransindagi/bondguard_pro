from datetime import date
from enum import Enum

import pandas as pd
from app.risk_engine.historical import FactorAlignmentService
from pydantic import BaseModel
from sqlalchemy.orm import Session


class ModelStatus(str, Enum):
    FULL_FACTOR_MODEL = "FULL_FACTOR_MODEL"
    RATE_ONLY_MODEL = "RATE_ONLY_MODEL"
    UNAVAILABLE = "UNAVAILABLE"

class ModelAvailabilityResult(BaseModel):
    model_status: ModelStatus
    model_type: str = "Historical Simulation VaR"
    observation_count: int
    rate_panel_observation_count: int
    full_factor_panel_observation_count: int
    minimum_required_observations: int
    history_start_date: date | None
    history_end_date: date | None
    included_factors: list[str]
    excluded_factors: list[str]
    limitations: str



def check_model_availability(db: Session, min_required: int = 252) -> ModelAvailabilityResult:
    from app.data_quality.engine import DataQualityEngine

    # Check quality gate for Treasury rates
    rates_failed = False
    for rate_key in ["DGS2", "DGS5", "DGS10", "DGS30"]:
        if DataQualityEngine.check_dataset_gating(db, rate_key) == "FAIL":
            rates_failed = True
            break

    # Check quality gate for credit spreads
    spreads_failed = False
    for spread_key in ["BAMLC0A0CM", "BAMLH0A0HYM2"]:
        if DataQualityEngine.check_dataset_gating(db, spread_key) == "FAIL":
            spreads_failed = True
            break

    service = FactorAlignmentService(db)
    
    try:
        if rates_failed:
            rate_shocks = pd.DataFrame()
        else:
            rate_shocks = service.get_aligned_factor_returns(required_obs=1, model_status="RATE_ONLY_MODEL", include_etfs=False)
    except Exception:
        rate_shocks = pd.DataFrame()
        
    try:
        if rates_failed or spreads_failed:
            full_shocks = pd.DataFrame()
        else:
            full_shocks = service.get_aligned_factor_returns(required_obs=1, model_status="FULL_FACTOR_MODEL", include_etfs=False)
    except Exception:
        full_shocks = pd.DataFrame()
        
    rate_count = len(rate_shocks)
    full_count = len(full_shocks)
    
    if rate_count < min_required:
        return ModelAvailabilityResult(
            model_status=ModelStatus.UNAVAILABLE,
            observation_count=rate_count,
            rate_panel_observation_count=rate_count,
            full_factor_panel_observation_count=full_count,
            minimum_required_observations=min_required,
            history_start_date=pd.to_datetime(rate_shocks.index.min()).date() if not rate_shocks.empty else None,
            history_end_date=pd.to_datetime(rate_shocks.index.max()).date() if not rate_shocks.empty else None,
            included_factors=[],
            excluded_factors=["Treasury Rates", "Credit Spreads"],
            limitations="Insufficient aligned history for required rate factors. No VaR can be calculated."
        )
        
    if full_count >= min_required:
        return ModelAvailabilityResult(
            model_status=ModelStatus.FULL_FACTOR_MODEL,
            observation_count=full_count,
            rate_panel_observation_count=rate_count,
            full_factor_panel_observation_count=full_count,
            minimum_required_observations=min_required,
            history_start_date=pd.to_datetime(full_shocks.index.min()).date() if not full_shocks.empty else None,
            history_end_date=pd.to_datetime(full_shocks.index.max()).date() if not full_shocks.empty else None,
            included_factors=["Treasury Rates", "Credit Spreads"],
            excluded_factors=[],
            limitations="None."
        )
        
    return ModelAvailabilityResult(
        model_status=ModelStatus.RATE_ONLY_MODEL,
        observation_count=rate_count,
        rate_panel_observation_count=rate_count,
        full_factor_panel_observation_count=full_count,
        minimum_required_observations=min_required,
        history_start_date=pd.to_datetime(rate_shocks.index.min()).date() if not rate_shocks.empty else None,
        history_end_date=pd.to_datetime(rate_shocks.index.max()).date() if not rate_shocks.empty else None,
        included_factors=["Treasury Rates"],
        excluded_factors=["Credit Spreads"],
        limitations="Insufficient credit-spread history. Credit spread risk is excluded."
    )
