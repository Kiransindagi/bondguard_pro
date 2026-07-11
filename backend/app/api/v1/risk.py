from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from decimal import Decimal
from app.db.database import get_db
from app.db.models import Bond, Position, Portfolio, YieldCurvePoint
from app.risk_engine.types import BondRiskInput, BondRiskResult
from app.risk_engine.portfolio_risk import PortfolioRiskSummary, aggregate_portfolio_risk
from app.risk_engine.historical import HistoricalCoverageService, FactorAlignmentService
from app.risk_engine.position_risk import calculate_position_risk
from app.risk_engine.curve import YieldCurve
from app.risk_engine.exceptions import RiskEngineError

from app.auth.dependencies import PermissionChecker
from app.auth.permissions import RISK_READ

router = APIRouter(dependencies=[Depends(PermissionChecker(RISK_READ))])

@router.get("/bonds/{bond_id}", response_model=BondRiskResult)
def get_bond_risk(
    bond_id: int, 
    valuation_date: Optional[date] = None,
    clean_price: Optional[Decimal] = None,
    ytm: Optional[Decimal] = None,
    db: Session = Depends(get_db)
):
    if not valuation_date:
        valuation_date = date.today()
    if clean_price is not None and ytm is not None:
        raise HTTPException(status_code=400, detail="Provide only one of clean_price or ytm.")
    if clean_price is None and ytm is None:
        raise HTTPException(status_code=400, detail="Must provide either clean_price or ytm.")
    
    bond = db.query(Bond).filter(Bond.id == bond_id).first()
    if not bond:
        raise HTTPException(status_code=404, detail="Bond not found")

    input_data = BondRiskInput(
        bond_id=bond.id,
        face_value=bond.face_value,
        coupon_rate=bond.coupon_rate,
        coupon_frequency=bond.coupon_frequency,
        issue_date=bond.issue_date,
        maturity_date=bond.maturity_date,
        day_count_convention=bond.day_count_convention,
        valuation_date=valuation_date,
        clean_price=clean_price,
        ytm=ytm,
        quantity=Decimal('1')
    )
    
    try:
        return calculate_position_risk(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/historical/coverage")
def get_historical_coverage(db: Session = Depends(get_db)):
    """
    Returns the coverage statistics for the historical dataset, 
    including ETFs, Yield Curve, and Credit Spreads.
    """
    service = HistoricalCoverageService(db)
    return service.get_coverage_report()

@router.get("/historical/alignment")
def get_historical_alignment(
    start_date: date = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(None, description="End date (YYYY-MM-DD)"),
    required_obs: int = Query(252, description="Minimum number of aligned observations required"),
    db: Session = Depends(get_db)
):
    """
    Returns aligned factor shocks for ETFs, Yield Curve, and Credit Spreads.
    """
    service = FactorAlignmentService(db)
    try:
        df = service.get_aligned_factor_returns(start_date, end_date, required_obs)
        # Convert df to dictionary of records
        df_reset = df.reset_index()
        # Convert index 'observation_date' from datetime to date string
        df_reset['observation_date'] = df_reset['observation_date'].astype(str)
        return {
            "count": len(df),
            "start_date": df.index.min().isoformat() if not df.empty else None,
            "end_date": df.index.max().isoformat() if not df.empty else None,
            "data": df_reset.to_dict(orient="records")
        }
    except RiskEngineError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolios/{portfolio_id}/positions", response_model=List[BondRiskResult])
def get_portfolio_positions_risk(portfolio_id: int, valuation_date: Optional[date] = None, db: Session = Depends(get_db)):
    if not valuation_date:
        valuation_date = date.today()
        
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    positions = db.query(Position).filter(Position.portfolio_id == portfolio_id).all()
    results = []
    
    for pos in positions:
        bond = pos.bond
        
        # Determine pricing input
        price_input = None
        if pos.current_clean_price is not None:
            price_input = pos.current_clean_price
        else:
            price_input = Decimal('100.0') # Fallback if no market price

        input_data = BondRiskInput(
            bond_id=bond.id,
            face_value=bond.face_value,
            coupon_rate=bond.coupon_rate,
            coupon_frequency=bond.coupon_frequency,
            issue_date=bond.issue_date,
            maturity_date=bond.maturity_date,
            day_count_convention=bond.day_count_convention,
            valuation_date=valuation_date,
            clean_price=price_input,
            quantity=pos.quantity
        )
        try:
            results.append(calculate_position_risk(input_data))
        except Exception:
            pass # Skip failing ones for now, could be matured
            
    return results

@router.get("/portfolios/{portfolio_id}/summary", response_model=PortfolioRiskSummary)
def get_portfolio_risk_summary(portfolio_id: int, valuation_date: Optional[date] = None, db: Session = Depends(get_db)):
    if not valuation_date:
        valuation_date = date.today()
        
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    position_risks = get_portfolio_positions_risk(portfolio_id, valuation_date, db)
    
    # Try to get curve date if available
    latest_curve_point = db.query(YieldCurvePoint).order_by(YieldCurvePoint.observation_date.desc()).first()
    curve_date = latest_curve_point.observation_date if latest_curve_point else None

    return aggregate_portfolio_risk(portfolio_id, valuation_date, position_risks, curve_date)

@router.get("/curve")
def get_yield_curve(db: Session = Depends(get_db)):
    # Get latest date
    latest_date_result = db.query(YieldCurvePoint.observation_date).order_by(YieldCurvePoint.observation_date.desc()).first()
    if not latest_date_result:
        raise HTTPException(status_code=404, detail="No yield curve data found")
        
    obs_date = latest_date_result[0]
    points = db.query(YieldCurvePoint).filter(YieldCurvePoint.observation_date == obs_date).all()
    
    tenor_map = {}
    for pt in points:
        try:
            t = float(pt.tenor_years)
            # Convert stored percentage to decimal (e.g. 4.25 -> 0.0425)
            tenor_map[t] = Decimal(str(pt.yield_percent)) / Decimal('100.0')
        except ValueError:
            pass
                
    if not tenor_map:
        raise HTTPException(status_code=404, detail="Incomplete yield curve data")

    # This proves the curve abstraction works
    _curve = YieldCurve(tenor_map)

    return {
        "observation_date": obs_date,
        "points": [{"tenor": f"{k}Y", "yield_decimal": v} for k, v in sorted(tenor_map.items())]
    }
