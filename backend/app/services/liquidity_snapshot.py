import logging
from datetime import date
from decimal import Decimal

from app.db.models import (
    LiquidityAssumption,
    LiquidityPositionResult,
    LiquiditySnapshot,
    Portfolio,
    Position,
)
from app.risk_engine.liquidity_risk import (
    LiquidityAssumptionConfig,
    aggregate_portfolio_liquidity,
    calculate_position_liquidity,
)
from app.risk_engine.liquidity_risk.types import StressScenarioType
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def generate_liquidity_snapshot(db: Session, portfolio_id: int, valuation_date: date, assumption_id: int | None = None) -> LiquiditySnapshot:
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise ValueError("Portfolio not found")

    if assumption_id:
        assumption = db.query(LiquidityAssumption).filter(LiquidityAssumption.id == assumption_id).first()
    else:
        assumption = db.query(LiquidityAssumption).filter(LiquidityAssumption.is_active.is_(True)).order_by(LiquidityAssumption.id.desc()).first()

    if not assumption:
        raise ValueError("No active liquidity assumption found")

    config = LiquidityAssumptionConfig(**assumption.configuration_json)

    positions = db.query(Position).filter(Position.portfolio_id == portfolio_id).all()

    total_mv = sum(p.market_value or Decimal(0) for p in positions)
    
    pos_results_db = []
    pos_results_calc = []

    try:
        for p in positions:
            if not p.market_value or p.market_value <= 0:
                continue

            bond = p.bond
            weight = float(p.market_value / total_mv) if total_mv > 0 else 0.0

            res = calculate_position_liquidity(
                bond_type=bond.bond_type,
                rating=bond.credit_rating,
                years_to_maturity=max(0, (bond.maturity_date - valuation_date).days / 365.25),
                market_value=p.market_value,
                portfolio_weight=weight,
                config=config,
                scenario=StressScenarioType.NORMAL
            )

            res['bond_name'] = bond.bond_name
            res['market_value'] = p.market_value
            pos_results_calc.append(res)
            
            db_res = LiquidityPositionResult(
                position_id=p.id,
                bond_id=bond.id,
                market_value=p.market_value,
                liquidity_score=res['liquidity_score'],
                liquidity_class=res['liquidity_class'],
                estimated_bid_ask_bps=res['estimated_bid_ask_bps'],
                estimated_liquidation_cost=res['estimated_liquidation_cost'],
                model_daily_capacity=res['model_daily_capacity'],
                participation_rate=res['participation_rate'],
                raw_days_to_liquidate=res['raw_days_to_liquidate'],
                estimated_trading_days_to_liquidate=res['estimated_trading_days_to_liquidate'],
                liquidation_horizon_bucket=res['liquidation_horizon_bucket'],
                source_type="MODEL_ESTIMATE",
                methodology=assumption.methodology
            )
            pos_results_db.append(db_res)

        agg = aggregate_portfolio_liquidity(pos_results_calc)

        snapshot = LiquiditySnapshot(
            portfolio_id=portfolio_id,
            valuation_date=valuation_date,
            assumption_id=assumption.id,
            portfolio_market_value=agg['portfolio_market_value'],
            weighted_liquidity_score=agg['weighted_liquidity_score'],
            estimated_liquidation_cost=agg['estimated_total_liquidation_cost'],
            estimated_liquidation_cost_bps=agg['estimated_total_liquidation_cost_bps'],
            weighted_days_to_liquidate=agg['weighted_days_to_liquidate'],
            max_days_to_liquidate=agg['maximum_days_to_liquidate'],
            very_low_liquidity_market_value=agg['very_low_liquidity_market_value'],
            very_low_liquidity_weight=agg['very_low_liquidity_weight']
        )
        db.add(snapshot)
        db.flush()

        for db_res in pos_results_db:
            db_res.liquidity_snapshot_id = snapshot.id
            db.add(db_res)

        # TODO: Concentration snapshots could be added here to be fully atomic.
        
        db.commit()
        db.refresh(snapshot)
        return snapshot

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to generate liquidity snapshot: {e}")
        raise ValueError(f"Snapshot generation failed: {e}")
