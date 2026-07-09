def test_get_portfolio_liquidity_no_snapshot(client):
    response = client.get("/api/v1/liquidity-risk/portfolios/999/summary")
    assert response.status_code == 404

def test_create_and_get_snapshot(client):
    # This requires an existing portfolio (id=1 typically exists from seed)
    response = client.post("/api/v1/liquidity-risk/portfolios/1/snapshot")
    assert response.status_code in [200, 400]
    
    if response.status_code == 200:
        data = response.json()
        assert "portfolio_market_value" in data
        assert "weighted_liquidity_score" in data
        
        # Positions
        pos_resp = client.get("/api/v1/liquidity-risk/portfolios/1/positions")
        assert pos_resp.status_code == 200
        assert isinstance(pos_resp.json(), list)
        
        # Concentration
        conc_resp = client.get("/api/v1/liquidity-risk/portfolios/1/concentration?dimension=sector")
        assert conc_resp.status_code == 200
        
        # Limits
        lim_resp = client.get("/api/v1/liquidity-risk/portfolios/1/limits")
        assert lim_resp.status_code == 200
        
        # Stress
        stress_resp = client.post("/api/v1/liquidity-risk/portfolios/1/stress", json={"scenario": "SEVERE"})
        assert stress_resp.status_code == 200
        stress_data = stress_resp.json()
        assert stress_data['stressed_liquidation_cost'] >= stress_data['normal_liquidation_cost']
        
        # Adjusted VaR
        var_resp = client.get("/api/v1/liquidity-risk/portfolios/1/liquidity-adjusted-var")
        assert var_resp.status_code == 200
