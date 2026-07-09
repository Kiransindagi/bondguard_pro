from app.risk_engine.stress_testing.curve_shocks import interpolate_rate_shock
from app.risk_engine.stress_testing.spread_shocks import resolve_spread_shock
from app.db.models import Bond

def test_interpolate_rate_shock_exact_points():
    assert interpolate_rate_shock(2.0, 10, 20, 30, 40) == 10.0
    assert interpolate_rate_shock(5.0, 10, 20, 30, 40) == 20.0
    assert interpolate_rate_shock(10.0, 10, 20, 30, 40) == 30.0
    assert interpolate_rate_shock(30.0, 10, 20, 30, 40) == 40.0

def test_interpolate_rate_shock_intermediate():
    # Between 10 and 30
    assert interpolate_rate_shock(20.0, 10, 20, 30, 40) == 35.0

def test_resolve_spread_shock_unrecognized_rating():
    # Unrecognized rating defaults to IG shock
    bond = Bond(bond_type="Corporate", credit_rating="UNKNOWN")
    assert resolve_spread_shock(bond, 15, 80) == 15

def test_resolve_spread_shock_petrobras_special():
    # Petrobras should be HY regardless
    bond = Bond(bond_type="Corporate", bond_name="Petrobras Global Finance", credit_rating="BBB")
    assert resolve_spread_shock(bond, 15, 80) == 80

def test_compare_scenarios_empty_list(client):
    res = client.post("/api/v1/stress-tests/portfolios/1/compare", json={"scenario_ids": []})
    # Should probably just return empty list or fail gracefully depending on implementation
    assert res.status_code == 200
    assert len(res.json()["scenarios"]) == 0
