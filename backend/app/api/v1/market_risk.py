from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from decimal import Decimal
from app.db.database import get_db
from app.db.models import Portfolio
from app.risk_engine.position_risk import calculate_position_risk
from app.risk_engine.types import BondRiskInput
from app.risk_engine.historical import FactorAlignmentService
from app.risk_engine.market_risk import (
    check_model_availability,
    ModelStatus,
    ScenarioPnlMatrix,
    calculate_historical_var,
    calculate_expected_shortfall,
    calculate_parametric_var,
    calculate_covariance_matrix,
    calculate_correlation_matrix,
    calculate_component_var,
    calculate_marginal_var,
    calculate_rolling_volatility,
    calculate_backtest
)
import pandas as pd
import numpy as np

router = APIRouter()

@router.get("/portfolios/{portfolio_id}/availability")
def get_availability(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return check_model_availability(db, min_required=252)

def _get_portfolio_and_shocks(portfolio_id: int, db: Session, required_obs: int = 252, include_etfs: bool = True):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    availability = check_model_availability(db, min_required=required_obs)
    if availability.model_status == ModelStatus.UNAVAILABLE:
        raise HTTPException(status_code=400, detail=availability.limitations)
        
    service = FactorAlignmentService(db)
    try:
        shocks = service.get_aligned_factor_returns(
            required_obs=required_obs, 
            model_status=availability.model_status.value,
            include_etfs=include_etfs
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    return portfolio, shocks, availability

def _get_portfolio_positions_risk(portfolio, valuation_date: date) -> List:
    # Need to calculate position risk for each position
    position_risks = []
    for pos in portfolio.positions:
        bond = pos.bond
        input_data = BondRiskInput(
            bond_id=bond.id,
            face_value=bond.face_value,
            coupon_rate=bond.coupon_rate,
            coupon_frequency=bond.coupon_frequency,
            issue_date=bond.issue_date,
            maturity_date=bond.maturity_date,
            day_count_convention=bond.day_count_convention,
            valuation_date=valuation_date,
            clean_price=Decimal('100.0'), # rough approximation since we don't fetch live price here
            ytm=None,
            quantity=pos.quantity
        )
        try:
            position_risks.append(calculate_position_risk(input_data))
        except Exception:
            pass
    return position_risks

@router.get("/portfolios/{portfolio_id}/historical-var")
def get_historical_var(
    portfolio_id: int, 
    confidence_level: float = Query(0.95), 
    horizon_days: int = Query(1),
    db: Session = Depends(get_db)
):
    portfolio, shocks, availability = _get_portfolio_and_shocks(portfolio_id, db)
    
    position_risks = _get_portfolio_positions_risk(portfolio, date.today())
    bonds_map = {p.bond_id: p.bond for p in portfolio.positions}
    
    matrix_service = ScenarioPnlMatrix(shocks)
    pnl_matrix = matrix_service.compute_matrix(position_risks, bonds_map)
    
    # Simple horizon scaling if > 1 (just multiply by sqrt(t) for demo, historical overlapping windows is better)
    horizon_scale = np.sqrt(horizon_days)
    
    total_pnl = pnl_matrix["PORTFOLIO"].values * horizon_scale
    var_value = calculate_historical_var(total_pnl, confidence_level)
    
    return {
        "var_currency": var_value,
        "confidence_level": confidence_level,
        "horizon_days": horizon_days,
        "method": "Historical Simulation",
        "observation_count": len(total_pnl),
        "model_type": availability.model_status.value
    }

@router.get("/portfolios/{portfolio_id}/parametric-var")
def get_parametric_var(
    portfolio_id: int, 
    confidence_level: float = Query(0.95), 
    horizon_days: int = Query(1),
    db: Session = Depends(get_db)
):
    portfolio, shocks, availability = _get_portfolio_and_shocks(portfolio_id, db)
    
    position_risks = _get_portfolio_positions_risk(portfolio, date.today())
    bonds_map = {p.bond_id: p.bond for p in portfolio.positions}
    
    matrix_service = ScenarioPnlMatrix(shocks)
    pnl_matrix = matrix_service.compute_matrix(position_risks, bonds_map)
    
    # We can approximate exposures via the standard deviation of each position's PnL? 
    # Or properly w^T Sigma w using actual exposures.
    # The PnL matrix cov is already w^T Sigma w implicitly because cols are PnL of each pos.
    pos_cols = [col for col in pnl_matrix.columns if col != "PORTFOLIO"]
    cov = pnl_matrix[pos_cols].cov().values
    
    # exposures are just 1s since columns are ALREADY in currency PnL!
    exp = np.ones(len(pos_cols))
    var_1d = calculate_parametric_var(exp, cov, confidence_level)
    
    var_currency = var_1d * np.sqrt(horizon_days)
    
    return {
        "var_currency": var_currency,
        "confidence_level": confidence_level,
        "horizon_days": horizon_days,
        "method": "Parametric",
        "observation_count": len(shocks),
        "model_type": availability.model_status.value
    }
    
@router.get("/factors/correlation")
def get_factor_correlation(matrix_type: str = Query("production_factors", description="Type of matrix: production_factors or etf_context"), db: Session = Depends(get_db)):
    service = FactorAlignmentService(db)
    include_etfs = matrix_type == "etf_context"
    try:
        shocks = service.get_aligned_factor_returns(required_obs=100, model_status="FULL_FACTOR_MODEL" if matrix_type == "production_factors" else "UNAVAILABLE", include_etfs=include_etfs)
        
        # If production factors, we must drop ETFs
        if matrix_type == "production_factors":
            shocks = shocks[[c for c in shocks.columns if c.startswith("RATE_") or c.startswith("SPREAD_")]]
        else:
            shocks = shocks[[c for c in shocks.columns if not (c.startswith("RATE_") or c.startswith("SPREAD_"))]]
            
        return calculate_correlation_matrix(shocks)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/factors/covariance")
def get_factor_covariance(matrix_type: str = Query("production_factors", description="Type of matrix: production_factors or etf_context"), db: Session = Depends(get_db)):
    service = FactorAlignmentService(db)
    include_etfs = matrix_type == "etf_context"
    try:
        shocks = service.get_aligned_factor_returns(required_obs=100, model_status="FULL_FACTOR_MODEL" if matrix_type == "production_factors" else "UNAVAILABLE", include_etfs=include_etfs)
        
        if matrix_type == "production_factors":
            shocks = shocks[[c for c in shocks.columns if c.startswith("RATE_") or c.startswith("SPREAD_")]]
        else:
            shocks = shocks[[c for c in shocks.columns if not (c.startswith("RATE_") or c.startswith("SPREAD_"))]]
            
        return calculate_covariance_matrix(shocks)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
@router.get("/portfolios/{portfolio_id}/expected-shortfall")
def get_expected_shortfall(
    portfolio_id: int, 
    confidence_level: float = Query(0.95), 
    db: Session = Depends(get_db)
):
    portfolio, shocks, availability = _get_portfolio_and_shocks(portfolio_id, db, required_obs=252, include_etfs=False)
    
    position_risks = _get_portfolio_positions_risk(portfolio, date.today())
    bonds_map = {p.bond_id: p.bond for p in portfolio.positions}
    
    matrix_service = ScenarioPnlMatrix(shocks)
    pnl_matrix = matrix_service.compute_matrix(position_risks, bonds_map)
    
    total_pnl = pnl_matrix["PORTFOLIO"].values
    es_value = calculate_expected_shortfall(total_pnl, confidence_level)
    
    return {
        "expected_shortfall_currency": es_value,
        "confidence_level": confidence_level,
        "observation_count": len(total_pnl),
        "model_type": availability.model_status.value
    }
    
@router.get("/portfolios/{portfolio_id}/contributions")
def get_contributions(
    portfolio_id: int, 
    db: Session = Depends(get_db)
):
    portfolio, shocks, availability = _get_portfolio_and_shocks(portfolio_id, db, required_obs=252, include_etfs=False)
    
    position_risks = _get_portfolio_positions_risk(portfolio, date.today())
    bonds_map = {p.bond_id: p.bond for p in portfolio.positions}
    
    matrix_service = ScenarioPnlMatrix(shocks)
    pnl_matrix = matrix_service.compute_matrix(position_risks, bonds_map)
    
    pos_cols = [col for col in pnl_matrix.columns if col != "PORTFOLIO"]
    cov = pnl_matrix[pos_cols].cov().values
    exp = np.ones(len(pos_cols))
    
    var_currency = calculate_parametric_var(exp, cov, 0.95)
    comp_var = calculate_component_var(exp, cov, var_currency)
    marg_var = calculate_marginal_var(exp, cov, var_currency)
    
    results = []
    for idx, bond_id in enumerate(pos_cols):
        cv = float(comp_var[idx])
        pct = float(cv / var_currency * 100.0) if var_currency else 0.0
        results.append({
            "bond_id": bond_id,
            "component_var_currency": cv,
            "contribution_percent": pct,
            "marginal_var": float(marg_var[idx])
        })
        
    return {
        "method": "Parametric Component VaR",
        "total_var": var_currency,
        "model_type": availability.model_status.value,
        "contributions": results
    }

@router.get("/factors/volatility")
def get_factor_volatility(
    window: int = Query(252),
    matrix_type: str = Query("production_factors"),
    db: Session = Depends(get_db)
):
    service = FactorAlignmentService(db)
    include_etfs = matrix_type == "etf_context"
    
    if include_etfs:
        try:
            shocks = service.get_aligned_factor_returns(required_obs=window, model_status="UNAVAILABLE", include_etfs=True)
            etf_shocks = shocks[[c for c in shocks.columns if not (c.startswith("RATE_") or c.startswith("SPREAD_"))]]
            return calculate_rolling_volatility(etf_shocks, window=window)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # production_factors
        # Get rate shocks independently
        try:
            rate_shocks = service.get_aligned_factor_returns(required_obs=window, model_status="RATE_ONLY_MODEL", include_etfs=False)
            rate_shocks = rate_shocks[[c for c in rate_shocks.columns if c.startswith("RATE_")]]
        except Exception:
            rate_shocks = pd.DataFrame()
            
        # Get full shocks to extract spreads independently
        try:
            # For spread volatility, window could be smaller if we want to show it, 
            # but user said 'insufficient spread history must not prevent rate volatility'
            full_shocks = service.get_aligned_factor_returns(required_obs=1, model_status="FULL_FACTOR_MODEL", include_etfs=False)
            spread_shocks = full_shocks[[c for c in full_shocks.columns if c.startswith("SPREAD_")]]
        except Exception:
            spread_shocks = pd.DataFrame()
            
        if rate_shocks.empty and spread_shocks.empty:
            raise HTTPException(status_code=400, detail="Insufficient history for all production factors.")
            
        # We can just return rate rolling volatility, and spread rolling volatility separately, or joined outer.
        # But rolling volatility drops NAs across columns if joined before.
        # Better to calculate rolling independently and join!
        rate_vol = rate_shocks.rolling(window=window).std().dropna(how='all') if not rate_shocks.empty else pd.DataFrame()
        spread_vol = spread_shocks.rolling(window=window).std().dropna(how='all') if not spread_shocks.empty else pd.DataFrame()
        
        # Outer join the results
        combined_vol = rate_vol.join(spread_vol, how='outer') if not rate_vol.empty else spread_vol
        combined_vol = combined_vol.dropna(how='all')
        
        if combined_vol.empty:
             raise HTTPException(status_code=400, detail="Insufficient history to compute volatility for requested window.")
             
        combined_reset = combined_vol.reset_index()
        combined_reset = combined_reset.replace({np.nan: None})
        
        return {
            "window": window,
            "data": combined_reset.to_dict(orient="records"),
            "warnings": "Spread history insufficient for requested window." if len(spread_shocks) < window else None
        }
        
@router.get("/portfolios/{portfolio_id}/backtest")
def get_backtest(
    portfolio_id: int, 
    confidence_level: float = Query(0.95), 
    db: Session = Depends(get_db)
):
    portfolio, shocks, availability = _get_portfolio_and_shocks(portfolio_id, db, required_obs=252, include_etfs=False)
    
    position_risks = _get_portfolio_positions_risk(portfolio, date.today())
    bonds_map = {p.bond_id: p.bond for p in portfolio.positions}
    
    matrix_service = ScenarioPnlMatrix(shocks)
    pnl_matrix = matrix_service.compute_matrix(position_risks, bonds_map)
    
    total_pnl = pnl_matrix["PORTFOLIO"].values
    return calculate_backtest(total_pnl, confidence_level=confidence_level, window=252)
