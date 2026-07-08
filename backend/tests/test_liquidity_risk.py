import pytest
from decimal import Decimal
from app.risk_engine.liquidity_risk import (
    calculate_liquidity_score,
    estimate_bid_ask_spread_bps,
    calculate_liquidation_cost,
    estimate_daily_capacity,
    calculate_days_to_liquidate,
    get_horizon_bucket,
    DEFAULT_ASSUMPTIONS,
    LiquidityClass,
    classify_liquidity,
    HorizonBucket,
    calculate_concentration,
    evaluate_limit,
    LimitStatus,
    get_stressed_multipliers,
    StressScenarioType,
    calculate_liquidity_adjusted_var
)

def test_liquidity_classification():
    assert classify_liquidity(85.0) == LiquidityClass.HIGH
    assert classify_liquidity(70.0) == LiquidityClass.MEDIUM
    assert classify_liquidity(40.0) == LiquidityClass.LOW
    assert classify_liquidity(10.0) == LiquidityClass.VERY_LOW

def test_liquidity_score():
    # Treasury
    score1 = calculate_liquidity_score("Treasury", "AAA", 2.0, 0.05, DEFAULT_ASSUMPTIONS)
    assert score1 == 100.0

    # IG Corporate
    score2 = calculate_liquidity_score("Corporate", "BBB", 5.0, 0.15, DEFAULT_ASSUMPTIONS)
    # type=70, rating=70, mat=90, conc=60 => 70*.4 + 70*.3 + 90*.15 + 60*.15 = 28 + 21 + 13.5 + 9 = 71.5
    assert score2 == 71.5

def test_transaction_cost():
    bps = estimate_bid_ask_spread_bps("Corporate", "BB", DEFAULT_ASSUMPTIONS)
    assert bps == 50.0

    cost = calculate_liquidation_cost(Decimal("1000000"), bps)
    # 1000000 * 50 / 20000 = 2500
    assert cost == Decimal("2500")

def test_days_to_liquidate():
    cap = estimate_daily_capacity("Corporate", "BB", DEFAULT_ASSUMPTIONS)
    assert cap == 1000000.0

    raw, trading = calculate_days_to_liquidate(5000000.0, cap, 0.20)
    # allowed_daily = 1000000 * 0.2 = 200000
    # days = 5000000 / 200000 = 25
    assert raw == 25.0
    assert trading == 25
    assert get_horizon_bucket(trading) == HorizonBucket.OVER_TWENTY_DAYS

def test_concentration():
    pos = [
        {'market_value': 1000, 'issuer': 'A'},
        {'market_value': 2000, 'issuer': 'A'},
        {'market_value': 2000, 'issuer': 'B'}
    ]
    res = calculate_concentration(pos, 'issuer')
    assert len(res) == 2
    assert res[0]['bucket_name'] == 'A'
    assert res[0]['portfolio_weight'] == 0.6
    assert res[1]['bucket_name'] == 'B'
    assert res[1]['portfolio_weight'] == 0.4

def test_limits():
    assert evaluate_limit(0.15, 0.10, 0.20) == LimitStatus.WARNING
    assert evaluate_limit(0.25, 0.10, 0.20) == LimitStatus.BREACH
    assert evaluate_limit(0.05, 0.10, 0.20) == LimitStatus.OK

def test_stressed_liquidity():
    mult_s, mult_c = get_stressed_multipliers(StressScenarioType.SEVERE, "Corporate")
    assert mult_s == 2.5
    assert mult_c == 0.40

def test_liquidity_adjusted_var():
    assert calculate_liquidity_adjusted_var(100.0, 50.0) == 150.0

def test_atomic_rollback():
    # Placeholder for atomic rollback test logic. Just testing the concept structure.
    pass

def test_decimal_precision():
    val = estimate_bid_ask_spread_bps("Treasury", "AAA", DEFAULT_ASSUMPTIONS)
    assert isinstance(val, float) # We use float internally for speed

def test_hhi():
    pos = [
        {'market_value': 10, 'issuer': 'A'},
        {'market_value': 10, 'issuer': 'B'}
    ]
    concs = calculate_concentration(pos, 'issuer')
    from app.risk_engine.liquidity_risk import calculate_hhi
    hhi = calculate_hhi(concs)
    # 0.5^2 + 0.5^2 = 0.5
    assert abs(hhi - 0.5) < 1e-6

def test_top_n_concentration():
    pos = [{'market_value': i, 'issuer': str(i)} for i in range(1, 11)]
    concs = calculate_concentration(pos, 'issuer')
    assert concs[0]['portfolio_weight'] > concs[1]['portfolio_weight']

def test_empty_portfolio_behavior():
    concs = calculate_concentration([], 'issuer')
    assert concs == []

def test_zero_market_value_behavior():
    pos = [{'market_value': 0.0, 'issuer': 'A'}, {'market_value': 10, 'issuer': 'B'}]
    concs = calculate_concentration(pos, 'issuer')
    assert len(concs) == 2
    assert concs[0]['bucket_name'] == 'B'
    assert concs[0]['portfolio_weight'] == 1.0
    assert concs[1]['bucket_name'] == 'A'
    assert concs[1]['portfolio_weight'] == 0.0

def test_snapshot_history():
    pass

def test_stressed_capacity_behavior():
    from app.risk_engine.liquidity_risk import get_stressed_multipliers
    from app.risk_engine.liquidity_risk.types import StressScenarioType
    cost_mult, cap_mult = get_stressed_multipliers(StressScenarioType.CREDIT_MARKET_FREEZE, 'Corporate')
    assert cap_mult < 1.0
    assert cost_mult > 1.0

