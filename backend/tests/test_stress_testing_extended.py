import pytest
from app.db.models import Bond
from app.risk_engine.stress_testing.curve_shocks import interpolate_rate_shock
from app.risk_engine.stress_testing.spread_shocks import resolve_spread_shock


def test_interpolate_rate_shock_boundaries():
    # 2Y bound
    shock_1y = interpolate_rate_shock(1.0, 10, 20, 30, 40)
    assert shock_1y == 10.0
    
    # 30Y bound
    shock_40y = interpolate_rate_shock(40.0, 10, 20, 30, 40)
    assert shock_40y == 40.0
    
    # Interpolation mid
    shock_7_5y = interpolate_rate_shock(7.5, 10, 20, 30, 40)
    assert shock_7_5y == 25.0

def test_resolve_spread_shock():
    # IG bond
    ig_bond = Bond(bond_type="Corporate", credit_rating="BBB")
    assert resolve_spread_shock(ig_bond, 50, 100) == 50
    
    # HY bond
    hy_bond = Bond(bond_type="Corporate", credit_rating="BB")
    assert resolve_spread_shock(hy_bond, 50, 100) == 100
    
    # Treasury bond
    tsy_bond = Bond(bond_type="Government", credit_rating="AAA")
    assert resolve_spread_shock(tsy_bond, 50, 100) == 0

def test_predefined_scenario_update_protection(client):
    scenarios = client.get("/api/v1/stress-scenarios").json()
    predefined = next(s for s in scenarios if s["is_predefined"])
    
    response = client.patch(f"/api/v1/stress-scenarios/{predefined['id']}", json={"rate_2y_shock_bps": 500})
    assert response.status_code == 400
    assert "Cannot modify predefined scenario" in response.text

def test_missing_scenario_handling(client):
    payload = {
        "scenario_id": 999999,
        "calculation_method": "FULL_REVALUATION"
    }
    response = client.post("/api/v1/stress-tests/portfolios/1/run", json=payload)
    assert response.status_code == 404
    assert "Scenario not found" in response.text

def test_approximation_vs_full_revaluation_diff(client):
    scenarios = client.get("/api/v1/stress-scenarios").json()
    scenario_id = next(s["id"] for s in scenarios if s["name"] == "RATE_UP_50BP")
    
    res_full = client.post("/api/v1/stress-tests/portfolios/1/run", json={
        "scenario_id": scenario_id,
        "calculation_method": "FULL_REVALUATION"
    }).json()
    
    res_approx = client.post("/api/v1/stress-tests/portfolios/1/run", json={
        "scenario_id": scenario_id,
        "calculation_method": "APPROXIMATION"
    }).json()
    
    # Check that they both result in losses
    assert res_full["total_pnl"] < 0
    assert res_approx["total_pnl"] < 0
    
    # Check that they are slightly different (due to convexity)
    assert abs(res_full["total_pnl"] - res_approx["total_pnl"]) > 0

def test_run_stress_test_zero_shock(client):
    # Create zero shock scenario
    payload = {
        "name": "ZERO_SHOCK",
        "scenario_type": "CUSTOM",
        "rate_2y_shock_bps": 0,
        "rate_5y_shock_bps": 0,
        "rate_10y_shock_bps": 0,
        "rate_30y_shock_bps": 0,
        "ig_spread_shock_bps": 0,
        "hy_spread_shock_bps": 0
    }
    create_res = client.post("/api/v1/stress-scenarios", json=payload)
    # Should fail as 0 shocks are invalid by API definition
    assert create_res.status_code == 400

def test_run_stress_test_extreme_shock_rejection(client):
    payload = {
        "name": "EXTREME_SHOCK",
        "scenario_type": "CUSTOM",
        "rate_2y_shock_bps": 5000,
        "rate_5y_shock_bps": 0,
        "rate_10y_shock_bps": 0,
        "rate_30y_shock_bps": 0,
        "ig_spread_shock_bps": 0,
        "hy_spread_shock_bps": 0
    }
    create_res = client.post("/api/v1/stress-scenarios", json=payload)
    assert create_res.status_code == 400

def test_stress_test_persistence_accuracy(client):
    scenarios = client.get("/api/v1/stress-scenarios").json()
    scenario_id = next(s["id"] for s in scenarios if s["name"] == "RATE_UP_25BP")
    
    run_res = client.post("/api/v1/stress-tests/portfolios/1/run", json={"scenario_id": scenario_id}).json()
    
    # Fetch from history
    hist_res = client.get(f"/api/v1/stress-tests/runs/{run_res['id']}").json()
    assert hist_res["scenario_id"] == scenario_id
    assert hist_res["total_pnl"] == pytest.approx(run_res["total_pnl"], abs=0.01)
    assert hist_res["total_loss_percent"] == run_res["total_loss_percent"]
    assert len(hist_res["positions"]) == len(run_res["positions"])
    assert hist_res["positions"][0]["pnl"] == pytest.approx(run_res["positions"][0]["pnl"], abs=0.01)

def test_get_invalid_run(client):
    res = client.get("/api/v1/stress-tests/runs/999999")
    assert res.status_code == 404

def test_compare_scenarios_ordering_accuracy(client):
    scenarios = client.get("/api/v1/stress-scenarios").json()
    s_ids = [s["id"] for s in scenarios if s["name"] in ["RATE_UP_100BP", "RATE_DOWN_100BP"]]
    
    res = client.post("/api/v1/stress-tests/portfolios/1/compare", json={"scenario_ids": s_ids}).json()
    scens = res["scenarios"]
    assert len(scens) == 2
    assert scens[0]["total_pnl"] <= scens[1]["total_pnl"] # Worst first

def test_portfolio_not_found_handling(client):
    scenarios = client.get("/api/v1/stress-scenarios").json()
    s_id = scenarios[0]["id"]
    
    res = client.post("/api/v1/stress-tests/portfolios/99999/run", json={"scenario_id": s_id})
    assert res.status_code == 404
