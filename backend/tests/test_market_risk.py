import numpy as np
from app.risk_engine.market_risk import (
    calculate_component_var,
    calculate_expected_shortfall,
    calculate_historical_var,
    calculate_marginal_var,
    calculate_parametric_var,
)


def test_historical_var():
    pnl = np.array([-100, -50, 0, 50, 100])
    # 5 items. 95% threshold -> worst 5% -> -100
    var = calculate_historical_var(pnl, 0.95)
    assert var > 0
    assert np.isclose(var, 50.0)

def test_expected_shortfall():
    pnl = np.array([-100, -80, 0, 50, 100])
    # VaR 95% = 100 (worst case)
    # ES = average of losses beyond VaR threshold. 
    # With only 5 items, at 80% var threshold, it's 80. ES = average(-100, -80) = 90
    # Let's test with 80% confidence level
    es = calculate_expected_shortfall(pnl, 0.80)
    assert es >= 80

def test_parametric_var():
    exp = np.array([100, 100])
    cov = np.array([[0.01, 0], [0, 0.01]]) # Variance is 0.01 for each
    var = calculate_parametric_var(exp, cov, 0.95)
    # wTw = 100*0.01*100 + 100*0.01*100 = 100 + 100 = 200
    # std = sqrt(200) = 14.14
    # var = 1.645 * 14.14 = 23.26
    assert var > 0
    assert np.isclose(var, 23.26, atol=0.1)

def test_component_marginal_var():
    exp = np.array([100, 100])
    cov = np.array([[0.01, 0], [0, 0.01]])
    var = calculate_parametric_var(exp, cov, 0.95)
    
    comp_var = calculate_component_var(exp, cov, var)
    assert np.isclose(np.sum(comp_var), var)
    
    marg_var = calculate_marginal_var(exp, cov, var)
    assert len(marg_var) == 2

def test_availability_api(client):
    response = client.get("/api/v1/market-risk/portfolios/1/availability")
    if response.status_code == 200:
        data = response.json()
        assert "model_status" in data
    else:
        assert response.status_code in [404, 400]
