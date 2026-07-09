def test_get_yield_curve(client):
    response = client.get("/api/v1/risk/curve")
    if response.status_code == 200:
        data = response.json()
        assert "observation_date" in data
        assert "points" in data
    else:
        assert response.status_code == 404

def test_bond_risk_invalid_params(client):
    response = client.get("/api/v1/risk/bonds/999")
    # Neither price nor yield
    assert response.status_code == 400

    response = client.get("/api/v1/risk/bonds/999?clean_price=100&ytm=0.05")
    # Both provided
    assert response.status_code == 400

def test_bond_risk_not_found(client):
    response = client.get("/api/v1/risk/bonds/999999?clean_price=100")
    assert response.status_code == 404

def test_portfolio_risk_empty(client):
    # Missing portfolio
    response = client.get("/api/v1/risk/portfolios/99999/summary")
    assert response.status_code == 404
