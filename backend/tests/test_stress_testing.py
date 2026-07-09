import uuid

def test_list_stress_scenarios(client):
    response = client.get("/api/v1/stress-scenarios")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 28 # Predefined scenarios


def test_create_custom_scenario(client):
    name = f"CUSTOM_TEST_{uuid.uuid4().hex[:8]}"
    payload = {
        "name": name,
        "description": "Test custom scenario",
        "scenario_type": "CUSTOM",
        "rate_2y_shock_bps": 100.0,
        "rate_5y_shock_bps": 100.0,
        "rate_10y_shock_bps": 100.0,
        "rate_30y_shock_bps": 100.0,
        "ig_spread_shock_bps": 50.0,
        "hy_spread_shock_bps": 100.0
    }
    response = client.post("/api/v1/stress-scenarios", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == name
    assert data["rate_10y_shock_bps"] == 100.0

def test_run_stress_test_full_reval(client):
    # GET scenario
    scenarios = client.get("/api/v1/stress-scenarios").json()
    scenario_id = next(s["id"] for s in scenarios if s["name"] == "RATE_UP_100BP")
    
    payload = {
        "scenario_id": scenario_id,
        "calculation_method": "FULL_REVALUATION"
    }
    response = client.post("/api/v1/stress-tests/portfolios/1/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "total_pnl" in data
    # Rate up 100 bps should cause a loss
    assert data["total_pnl"] < 0

def test_run_stress_test_approximation(client):
    # GET scenario
    scenarios = client.get("/api/v1/stress-scenarios").json()
    scenario_id = next(s["id"] for s in scenarios if s["name"] == "RATE_UP_100BP")
    
    payload = {
        "scenario_id": scenario_id,
        "calculation_method": "APPROXIMATION"
    }
    response = client.post("/api/v1/stress-tests/portfolios/1/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "total_pnl" in data
    # Rate up 100 bps should cause a loss
    assert data["total_pnl"] < 0

def test_run_stress_test_spread_widening(client):
    scenarios = client.get("/api/v1/stress-scenarios").json()
    scenario_id = next(s["id"] for s in scenarios if s["name"] == "HY_SPREAD_WIDEN_200BP")
    
    payload = {
        "scenario_id": scenario_id
    }
    response = client.post("/api/v1/stress-tests/portfolios/1/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "total_pnl" in data
    
    # Check that treasury position is unaffected by spread shock
    for pos in data["positions"]:
        if pos["rating"] == "AAA": # Treasury
            assert pos["spread_shock_bps"] == 0.0

def test_compare_stress_tests(client):
    scenarios = client.get("/api/v1/stress-scenarios").json()
    s1 = next(s["id"] for s in scenarios if s["name"] == "RATE_UP_100BP")
    s2 = next(s["id"] for s in scenarios if s["name"] == "RATE_UP_200BP")
    
    payload = {
        "scenario_ids": [s1, s2]
    }
    response = client.post("/api/v1/stress-tests/portfolios/1/compare", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["scenarios"]) == 2
    # The first should be RATE_UP_200BP as it is a larger loss
    assert data["scenarios"][0]["scenario_name"] == "RATE_UP_200BP"

def test_get_stress_history(client):
    response = client.get("/api/v1/stress-tests/portfolios/1/history")
    assert response.status_code == 200
    data = response.json()
    assert type(data) is list

def test_invalid_scenario_creation(client):
    payload = {
        "name": "INVALID",
        "scenario_type": "CUSTOM",
        "rate_2y_shock_bps": 0,
        "rate_5y_shock_bps": 0,
        "rate_10y_shock_bps": 0,
        "rate_30y_shock_bps": 0,
        "ig_spread_shock_bps": 0,
        "hy_spread_shock_bps": 0
    }
    response = client.post("/api/v1/stress-scenarios", json=payload)
    assert response.status_code == 400
    assert "At least one shock must be non-zero" in response.text

def test_delete_predefined_scenario(client):
    scenarios = client.get("/api/v1/stress-scenarios").json()
    s1 = next(s["id"] for s in scenarios if s["is_predefined"])
    response = client.delete(f"/api/v1/stress-scenarios/{s1}")
    assert response.status_code == 400
    assert "Cannot delete predefined scenario" in response.text
