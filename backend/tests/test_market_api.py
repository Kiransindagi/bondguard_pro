
def test_get_yield_curve_empty(client):
    response = client.get("/api/v1/market/yield-curve")
    assert response.status_code == 200
    assert response.json() == []

def test_get_prices_not_found(client):
    response = client.get("/api/v1/market/prices?symbol=INVALID")
    assert response.status_code == 404

def test_get_data_status(client):
    response = client.get("/api/v1/market/data-status")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
