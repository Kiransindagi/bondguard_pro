def test_get_historical_coverage(client):
    response = client.get("/api/v1/risk/historical/coverage")
    assert response.status_code == 200
    data = response.json()
    assert "etf_prices" in data
    assert "yield_curve" in data
    assert "credit_spreads" in data
    assert data["status"] == "ok"

def test_get_historical_alignment_insufficient_data(client):
    # Depending on DB state, this might fail with 400 Insufficient history or return data
    response = client.get("/api/v1/risk/historical/alignment?required_obs=99999")
    assert response.status_code == 400
    assert "Insufficient history" in response.json()["detail"]

