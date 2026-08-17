from datetime import date
from decimal import Decimal

from app.auth.dependencies import PermissionChecker
from app.auth.permissions import RISK_READ
from app.db.database import get_db
from app.db.models import Bond, Portfolio
from app.risk_engine.advanced_analytics import (
    AdvancedAnalyticsCalculator,
    CarryRollDownCalculator,
    PnLExplainCalculator,
)
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/bonds/{bond_id}/key-rate-duration", dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_bond_key_rate_duration(
    bond_id: int,
    valuation_date: date | None = None,
    clean_price: Decimal = Query(Decimal('100.0')),
    db: Session = Depends(get_db)
):
    bond = db.query(Bond).filter(Bond.id == bond_id).first()
    if not bond:
        raise HTTPException(status_code=404, detail="Bond not found")
        
    val_date = valuation_date or date.today()
    return AdvancedAnalyticsCalculator.calculate_key_rate_duration(
        bond=bond,
        valuation_date=val_date,
        clean_price=clean_price,
        quantity=Decimal(1)
    )

@router.get("/portfolios/{portfolio_id}/key-rate-duration", dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_portfolio_key_rate_duration(
    portfolio_id: int,
    valuation_date: date | None = None,
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    val_date = valuation_date or date.today()
    
    total_mv = 0.0
    weighted_krd = {"KRD_2Y": 0.0, "KRD_5Y": 0.0, "KRD_10Y": 0.0, "KRD_30Y": 0.0}
    
    for pos in portfolio.positions:
        bond = pos.bond
        price = pos.current_clean_price or Decimal('100.0')
        mv = float(pos.quantity) * float(bond.face_value) * (float(price) / 100.0)
        
        krd = AdvancedAnalyticsCalculator.calculate_key_rate_duration(
            bond=bond,
            valuation_date=val_date,
            clean_price=price,
            quantity=pos.quantity
        )
        
        total_mv += mv
        for k in weighted_krd:
            weighted_krd[k] += krd[k] * mv
            
    # Calculate average
    if total_mv > 0:
        for k in weighted_krd:
            weighted_krd[k] = round(weighted_krd[k] / total_mv, 6)
            
    return {
        "portfolio_id": portfolio_id,
        "key_rate_durations": weighted_krd,
        "total_market_value": total_mv
    }

@router.get("/portfolios/{portfolio_id}/bucketed-dv01", dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_portfolio_bucketed_dv01(
    portfolio_id: int,
    valuation_date: date | None = None,
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    val_date = valuation_date or date.today()
    
    total_dv01 = {"DV01_2Y": 0.0, "DV01_5Y": 0.0, "DV01_10Y": 0.0, "DV01_30Y": 0.0}
    
    for pos in portfolio.positions:
        bond = pos.bond
        price = pos.current_clean_price or Decimal('100.0')
        
        dv01_buckets = AdvancedAnalyticsCalculator.calculate_bucketed_dv01(
            bond=bond,
            valuation_date=val_date,
            clean_price=price,
            quantity=pos.quantity
        )
        
        for k in total_dv01:
            total_dv01[k] += dv01_buckets[k]
            
    # Round totals
    for k in total_dv01:
        total_dv01[k] = round(total_dv01[k], 2)
        
    return {
        "portfolio_id": portfolio_id,
        "bucketed_dv01": total_dv01
    }

@router.get("/portfolios/{portfolio_id}/spread-risk", dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_portfolio_spread_risk(
    portfolio_id: int,
    valuation_date: date | None = None,
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    val_date = valuation_date or date.today()
    
    portfolio_cs01 = 0.0
    ig_cs01 = 0.0
    hy_cs01 = 0.0
    sector_cs01 = {}
    
    for pos in portfolio.positions:
        bond = pos.bond
        price = pos.current_clean_price or Decimal('100.0')
        
        spread_info = AdvancedAnalyticsCalculator.calculate_spread_risk(
            bond=bond,
            valuation_date=val_date,
            clean_price=price,
            quantity=pos.quantity
        )
        
        cs01 = spread_info["cs01"]
        portfolio_cs01 += cs01
        
        rating = getattr(bond, "rating", "Unrated") or "Unrated"
        # Dummy classification for HY vs IG (IG is AAA to BBB, HY is BB and lower)
        is_hy = any(r in rating for r in ["BB", "B", "CCC", "CC", "C", "D"])
        
        if is_hy:
            hy_cs01 += cs01
        else:
            ig_cs01 += cs01
            
        sector = getattr(bond, "sector", "Government") or "Government"
        sector_cs01[sector] = sector_cs01.get(sector, 0.0) + cs01
        
    return {
        "portfolio_id": portfolio_id,
        "portfolio_cs01": round(portfolio_cs01, 2),
        "ig_cs01": round(ig_cs01, 2),
        "hy_cs01": round(hy_cs01, 2),
        "sector_cs01": {k: round(v, 2) for k, v in sector_cs01.items()}
    }

@router.get("/portfolios/{portfolio_id}/carry-roll-down", dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_portfolio_carry_roll_down(
    portfolio_id: int,
    valuation_date: date | None = None,
    horizon_months: int = Query(1),
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    val_date = valuation_date or date.today()
    
    total_mv = 0.0
    weighted_coupon_carry = 0.0
    weighted_yield_carry = 0.0
    weighted_roll_down = 0.0
    weighted_projected = 0.0
    
    for pos in portfolio.positions:
        bond = pos.bond
        price = pos.current_clean_price or Decimal('100.0')
        mv = float(pos.quantity) * float(bond.face_value) * (float(price) / 100.0)
        
        cr = CarryRollDownCalculator.calculate_carry_roll_down(
            db=db,
            bond=bond,
            valuation_date=val_date,
            clean_price=price,
            quantity=pos.quantity,
            horizon_months=horizon_months
        )
        
        total_mv += mv
        weighted_coupon_carry += cr["coupon_carry"] * mv
        weighted_yield_carry += cr["yield_carry"] * mv
        weighted_roll_down += cr["roll_down_return"] * mv
        weighted_projected += cr["projected_return"] * mv
        
    if total_mv > 0:
        weighted_coupon_carry /= total_mv
        weighted_yield_carry /= total_mv
        weighted_roll_down /= total_mv
        weighted_projected /= total_mv
        
    return {
        "portfolio_id": portfolio_id,
        "horizon_months": horizon_months,
        "coupon_carry": round(weighted_coupon_carry, 4),
        "yield_carry": round(weighted_yield_carry, 4),
        "roll_down_return": round(weighted_roll_down, 4),
        "projected_return": round(weighted_projected, 4),
        "total_market_value": total_mv
    }

@router.get("/portfolios/{portfolio_id}/pnl-explain", dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_portfolio_pnl_explain(
    portfolio_id: int,
    rate_shock_bps: float = Query(0.0),
    spread_shock_bps: float = Query(0.0),
    actual_pnl: float = Query(0.0),
    valuation_date: date | None = None,
    db: Session = Depends(get_db)
):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    val_date = valuation_date or date.today()
    
    totals = {
        "carry": 0.0,
        "rate_pnl": 0.0,
        "spread_pnl": 0.0,
        "convexity_pnl": 0.0,
        "explained_pnl": 0.0,
        "residual": 0.0,
        "actual_pnl": actual_pnl
    }
    
    # Run P&L explain for each position
    # If the user passed total portfolio actual_pnl, we distribute it or represent at portfolio level.
    # To be mathematically explicit, we sum the explain components across all positions.
    for pos in portfolio.positions:
        bond = pos.bond
        price = pos.current_clean_price or Decimal('100.0')
        
        # Position share of actual portfolio P&L (simple proportional proxy or 0 for detail check)
        pos_actual = 0.0
        
        exp = PnLExplainCalculator.calculate_pnl_explain(
            bond=bond,
            valuation_date=val_date,
            clean_price=price,
            quantity=pos.quantity,
            rate_shock_bps=rate_shock_bps,
            spread_shock_bps=spread_shock_bps,
            actual_pnl=pos_actual
        )
        
        totals["carry"] += exp["carry"]
        totals["rate_pnl"] += exp["rate_pnl"]
        totals["spread_pnl"] += exp["spread_pnl"]
        totals["convexity_pnl"] += exp["convexity_pnl"]
        totals["explained_pnl"] += exp["explained_pnl"]
        
    totals["residual"] = actual_pnl - totals["explained_pnl"]
    
    # Round all values
    for k in totals:
        totals[k] = round(totals[k], 2)
        
    return totals
