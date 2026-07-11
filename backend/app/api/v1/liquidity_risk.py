from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.db.database import get_db
from app.db.models import Portfolio, Position, LiquidityAssumption, LiquiditySnapshot, LiquidityPositionResult, ConcentrationLimit, Bond
from app.schemas.liquidity_risk import (
    PortfolioLiquidityResponse,
    PositionLiquidityResponse,
    LiquiditySnapshotResponse,
    HorizonDistribution,
    ConcentrationSummaryResponse,
    ConcentrationBreakdownItem,
    LimitUtilizationResponse,
    LiquidityAdjustedVaRResponse,
    LiquidityStressRequest,
    LiquidityStressResponse
)
from app.services.liquidity_snapshot import generate_liquidity_snapshot
from app.risk_engine.liquidity_risk import (
    calculate_concentration,
    calculate_hhi
)
from app.risk_engine.liquidity_risk.types import StressScenarioType, LimitStatus

from app.auth.dependencies import PermissionChecker
from app.auth.permissions import RISK_READ, LIQUIDITY_EXECUTE

router = APIRouter()

@router.get("/portfolios/{portfolio_id}/summary", response_model=PortfolioLiquidityResponse, dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_portfolio_liquidity_summary(portfolio_id: int, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
        
    snapshot = db.query(LiquiditySnapshot).filter(LiquiditySnapshot.portfolio_id == portfolio_id).order_by(LiquiditySnapshot.id.desc()).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No liquidity snapshot found for this portfolio")

    assumption = db.query(LiquidityAssumption).filter(LiquidityAssumption.id == snapshot.assumption_id).first()
    
    pos_results = db.query(LiquidityPositionResult).filter(LiquidityPositionResult.liquidity_snapshot_id == snapshot.id).all()
    
    buckets = {}
    for r in pos_results:
        b = r.liquidation_horizon_bucket
        buckets[b] = buckets.get(b, 0.0) + float(r.market_value)
    
    total_mv = float(snapshot.portfolio_market_value)
    dist = []
    if total_mv > 0:
        for b, mv in buckets.items():
            dist.append(HorizonDistribution(
                bucket=b,
                market_value=mv,
                percentage=mv/total_mv
            ))

    largest_illiquid = None
    if pos_results:
        illiquid_pos = [r for r in pos_results if r.liquidity_class == 'VERY_LOW']
        if illiquid_pos:
            largest = max(illiquid_pos, key=lambda x: float(x.market_value))
            bond = db.query(Bond).filter(Bond.id == largest.bond_id).first()
            largest_illiquid = bond.bond_name if bond else str(largest.bond_id)

    return PortfolioLiquidityResponse(
        portfolio_id=portfolio.id,
        portfolio_name=portfolio.name,
        valuation_date=snapshot.valuation_date,
        portfolio_market_value=float(snapshot.portfolio_market_value),
        weighted_liquidity_score=snapshot.weighted_liquidity_score,
        estimated_total_liquidation_cost=float(snapshot.estimated_liquidation_cost),
        estimated_total_liquidation_cost_bps=snapshot.estimated_liquidation_cost_bps,
        weighted_days_to_liquidate=snapshot.weighted_days_to_liquidate,
        maximum_days_to_liquidate=snapshot.max_days_to_liquidate,
        high_liquidity_weight=0.0, # calculate properly or store
        medium_liquidity_weight=0.0,
        low_liquidity_weight=0.0,
        very_low_liquidity_weight=snapshot.very_low_liquidity_weight,
        largest_illiquid_position=largest_illiquid,
        liquidation_horizon_distribution=dist,
        methodology=assumption.methodology if assumption else "Unknown",
        assumption_version=assumption.version if assumption else "Unknown",
        limitations="Model estimates based on characteristics proxy. Does not reflect real individual ADV."
    )

@router.get("/portfolios/{portfolio_id}/positions", response_model=List[PositionLiquidityResponse])
def get_portfolio_positions_liquidity(portfolio_id: int, db: Session = Depends(get_db)):
    snapshot = db.query(LiquiditySnapshot).filter(LiquiditySnapshot.portfolio_id == portfolio_id).order_by(LiquiditySnapshot.id.desc()).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No liquidity snapshot found")

    assumption = db.query(LiquidityAssumption).filter(LiquidityAssumption.id == snapshot.assumption_id).first()
    results = db.query(LiquidityPositionResult).filter(LiquidityPositionResult.liquidity_snapshot_id == snapshot.id).all()
    
    resp = []
    for r in results:
        bond = db.query(Bond).filter(Bond.id == r.bond_id).first()
        resp.append(PositionLiquidityResponse(
            position_id=r.position_id,
            bond_id=r.bond_id,
            bond_name=bond.bond_name,
            issuer=bond.issuer_name,
            rating=bond.credit_rating,
            sector=bond.sector,
            country=bond.country,
            maturity_date=bond.maturity_date,
            market_value=float(r.market_value),
            liquidity_score=r.liquidity_score,
            liquidity_class=r.liquidity_class,
            estimated_bid_ask_bps=r.estimated_bid_ask_bps,
            estimated_liquidation_cost=float(r.estimated_liquidation_cost),
            model_daily_capacity=float(r.model_daily_capacity),
            participation_rate=r.participation_rate,
            raw_days_to_liquidate=r.raw_days_to_liquidate,
            estimated_trading_days_to_liquidate=r.estimated_trading_days_to_liquidate,
            liquidation_horizon_bucket=r.liquidation_horizon_bucket,
            source_type=r.source_type,
            methodology=r.methodology,
            assumption_version=assumption.version if assumption else "Unknown",
            limitations="Model estimated"
        ))
    return resp

@router.get("/portfolios/{portfolio_id}/concentration", response_model=ConcentrationSummaryResponse)
def get_portfolio_concentration(portfolio_id: int, dimension: str = "issuer", db: Session = Depends(get_db)):
    positions = db.query(Position).filter(Position.portfolio_id == portfolio_id).all()
    if not positions:
        raise HTTPException(status_code=404, detail="No positions found")
    
    data = []
    for p in positions:
        if not p.market_value or p.market_value <= 0:
            continue
        bond = p.bond
        d_val = getattr(bond, 'issuer_name')
        if dimension == 'sector':
            d_val = bond.sector
        elif dimension == 'country':
            d_val = bond.country
        elif dimension == 'rating':
            d_val = bond.credit_rating
        elif dimension == 'bond_type':
            d_val = bond.bond_type
        elif dimension == 'maturity':
            days = (bond.maturity_date - date.today()).days
            if days <= 2*365:
                d_val = '0_TO_2Y'
            elif days <= 5*365:
                d_val = '2_TO_5Y'
            elif days <= 10*365:
                d_val = '5_TO_10Y'
            elif days <= 20*365:
                d_val = '10_TO_20Y'
            else:
                d_val = 'OVER_20Y'
            
        data.append({
            'market_value': float(p.market_value),
            'dimension_key': d_val
        })
        
    concs = calculate_concentration(data, 'dimension_key')
    hhi = calculate_hhi(concs)
    
    breakdown = []
    for i, c in enumerate(concs):
        breakdown.append(ConcentrationBreakdownItem(
            name=c['bucket_name'],
            market_value=c['market_value'],
            portfolio_weight=c['portfolio_weight'],
            position_count=c['position_count'],
            rank=i+1
        ))
        
    top_1 = concs[0]['portfolio_weight'] if len(concs) > 0 else 0.0
    top_3 = sum(c['portfolio_weight'] for c in concs[:3])
    top_5 = sum(c['portfolio_weight'] for c in concs[:5])
    
    return ConcentrationSummaryResponse(
        dimension=dimension,
        breakdown=breakdown,
        hhi=hhi,
        hhi_scaled=hhi * 10000,
        top_1_weight=top_1,
        top_3_weight=top_3,
        top_5_weight=top_5
    )

@router.post("/portfolios/{portfolio_id}/snapshot", response_model=LiquiditySnapshotResponse, dependencies=[Depends(PermissionChecker(LIQUIDITY_EXECUTE))])
def create_liquidity_snapshot(portfolio_id: int, assumption_id: int = None, db: Session = Depends(get_db)):
    try:
        snapshot = generate_liquidity_snapshot(db, portfolio_id, date.today(), assumption_id)
        
        assumption = db.query(LiquidityAssumption).filter(LiquidityAssumption.id == snapshot.assumption_id).first()
        pos_results = db.query(LiquidityPositionResult).filter(LiquidityPositionResult.liquidity_snapshot_id == snapshot.id).all()
        
        buckets = {}
        for r in pos_results:
            b = r.liquidation_horizon_bucket
            buckets[b] = buckets.get(b, 0.0) + float(r.market_value)
        
        total_mv = float(snapshot.portfolio_market_value)
        dist = []
        if total_mv > 0:
            for b, mv in buckets.items():
                dist.append(HorizonDistribution(
                    bucket=b,
                    market_value=mv,
                    percentage=mv/total_mv
                ))
                
        largest_illiquid = None
        if pos_results:
            illiquid_pos = [r for r in pos_results if r.liquidity_class == 'VERY_LOW']
            if illiquid_pos:
                largest = max(illiquid_pos, key=lambda x: float(x.market_value))
                bond = db.query(Bond).filter(Bond.id == largest.bond_id).first()
                largest_illiquid = bond.bond_name if bond else str(largest.bond_id)

        portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

        return LiquiditySnapshotResponse(
            id=snapshot.id,
            created_at=snapshot.created_at,
            portfolio_id=portfolio_id,
            portfolio_name=portfolio.name if portfolio else "Portfolio",
            valuation_date=snapshot.valuation_date,
            portfolio_market_value=total_mv,
            weighted_liquidity_score=snapshot.weighted_liquidity_score,
            estimated_total_liquidation_cost=float(snapshot.estimated_liquidation_cost),
            estimated_total_liquidation_cost_bps=snapshot.estimated_liquidation_cost_bps,
            weighted_days_to_liquidate=snapshot.weighted_days_to_liquidate,
            maximum_days_to_liquidate=snapshot.max_days_to_liquidate,
            high_liquidity_weight=0.0,
            medium_liquidity_weight=0.0,
            low_liquidity_weight=0.0,
            very_low_liquidity_weight=snapshot.very_low_liquidity_weight,
            largest_illiquid_position=largest_illiquid,
            liquidation_horizon_distribution=dist,
            methodology=assumption.methodology if assumption else "Unknown",
            assumption_version=assumption.version if assumption else "Unknown",
            limitations="Model estimated"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/portfolios/{portfolio_id}/limits", response_model=List[LimitUtilizationResponse], dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_portfolio_limits(portfolio_id: int, db: Session = Depends(get_db)):
    limits = db.query(ConcentrationLimit).filter(
        (ConcentrationLimit.portfolio_id == portfolio_id) | (ConcentrationLimit.portfolio_id.is_(None)),
        ConcentrationLimit.is_active.is_(True)
    ).all()
    
    # We would evaluate actual values here. For demonstration, we just return dummy actual values.
    # In a real system, you'd calculate the actual concentration first.
    resp = []
    for limit in limits:
        resp.append(LimitUtilizationResponse(
            limit=limit,
            actual_value=0.0,
            utilization_percent=0.0,
            status=LimitStatus.OK
        ))
    return resp

@router.post("/portfolios/{portfolio_id}/stress", response_model=LiquidityStressResponse, dependencies=[Depends(PermissionChecker(LIQUIDITY_EXECUTE))])
def stress_liquidity(portfolio_id: int, request: LiquidityStressRequest, db: Session = Depends(get_db)):
    snapshot = db.query(LiquiditySnapshot).filter(LiquiditySnapshot.portfolio_id == portfolio_id).order_by(LiquiditySnapshot.id.desc()).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No liquidity snapshot found")
        
    # In a full implementation, this would recalculate position_liquidity for each position with the requested scenario.
    # For now, we will return a mocked response based on the scenario type.
    mult = 1.0
    if request.scenario == StressScenarioType.MODERATE:
        mult = 1.5
    elif request.scenario == StressScenarioType.SEVERE:
        mult = 2.5
    elif request.scenario == StressScenarioType.CREDIT_MARKET_FREEZE:
        mult = 4.0
    
    normal_cost = float(snapshot.estimated_liquidation_cost)
    stressed_cost = normal_cost * mult
    
    return LiquidityStressResponse(
        scenario=request.scenario,
        normal_liquidation_cost=normal_cost,
        stressed_liquidation_cost=stressed_cost,
        incremental_liquidity_cost=stressed_cost - normal_cost,
        normal_days_to_liquidate=snapshot.weighted_days_to_liquidate,
        stressed_days_to_liquidate=snapshot.weighted_days_to_liquidate * (mult if mult > 1 else 1.2)
    )

@router.get("/portfolios/{portfolio_id}/liquidity-adjusted-var", response_model=LiquidityAdjustedVaRResponse, dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_liquidity_adjusted_var(portfolio_id: int, db: Session = Depends(get_db)):
    snapshot = db.query(LiquiditySnapshot).filter(LiquiditySnapshot.portfolio_id == portfolio_id).order_by(LiquiditySnapshot.id.desc()).first()
    if not snapshot:
        raise HTTPException(status_code=404, detail="No liquidity snapshot found")
        
    market_var = 10000.0 # Mocked VaR
    cost = float(snapshot.estimated_liquidation_cost)
    
    return LiquidityAdjustedVaRResponse(
        market_var=market_var,
        liquidity_cost_adjustment=cost,
        liquidity_adjusted_var=market_var + cost,
        confidence_level=0.99,
        horizon_days=1,
        market_risk_model_status="RATE_ONLY_MODEL",
        liquidity_methodology="CHARACTERISTIC_BASED_PROXY_V1",
        limitations="Market VaR excludes historical credit-spread VaR under current model availability."
    )

@router.get("/portfolios/{portfolio_id}/history", response_model=List[LiquiditySnapshotResponse], dependencies=[Depends(PermissionChecker(RISK_READ))])
def get_portfolio_liquidity_history(portfolio_id: int, db: Session = Depends(get_db)):
    snapshots = db.query(LiquiditySnapshot).filter(LiquiditySnapshot.portfolio_id == portfolio_id).order_by(LiquiditySnapshot.valuation_date.desc(), LiquiditySnapshot.id.desc()).all()
    resp = []
    for snapshot in snapshots:
        assumption = db.query(LiquidityAssumption).filter(LiquidityAssumption.id == snapshot.assumption_id).first()
        pos_results = db.query(LiquidityPositionResult).filter(LiquidityPositionResult.liquidity_snapshot_id == snapshot.id).all()
        buckets = {}
        for r in pos_results:
            b = r.liquidation_horizon_bucket
            buckets[b] = buckets.get(b, 0.0) + float(r.market_value)
        dist = []
        total_mv = float(snapshot.portfolio_market_value)
        if total_mv > 0:
            for b, mv in buckets.items():
                dist.append(HorizonDistribution(
                    bucket=b,
                    market_value=mv,
                    percentage=mv/total_mv
                ))
        largest_illiquid = None
        if pos_results:
            illiquid_pos = [r for r in pos_results if r.liquidity_class == 'VERY_LOW']
            if illiquid_pos:
                largest = max(illiquid_pos, key=lambda x: float(x.market_value))
                bond = db.query(Bond).filter(Bond.id == largest.bond_id).first()
                largest_illiquid = bond.bond_name if bond else str(largest.bond_id)
        
        resp.append(LiquiditySnapshotResponse(
            id=snapshot.id,
            created_at=snapshot.created_at,
            portfolio_id=portfolio_id,
            portfolio_name="Portfolio",
            valuation_date=snapshot.valuation_date,
            portfolio_market_value=total_mv,
            weighted_liquidity_score=snapshot.weighted_liquidity_score,
            estimated_total_liquidation_cost=float(snapshot.estimated_liquidation_cost),
            estimated_total_liquidation_cost_bps=snapshot.estimated_liquidation_cost_bps,
            weighted_days_to_liquidate=snapshot.weighted_days_to_liquidate,
            maximum_days_to_liquidate=snapshot.max_days_to_liquidate,
            high_liquidity_weight=0.0,
            medium_liquidity_weight=0.0,
            low_liquidity_weight=0.0,
            very_low_liquidity_weight=snapshot.very_low_liquidity_weight,
            largest_illiquid_position=largest_illiquid,
            liquidation_horizon_distribution=dist,
            methodology=assumption.methodology if assumption else "Unknown",
            assumption_version=assumption.version if assumption else "Unknown",
            limitations="Model estimated"
        ))
    return resp
