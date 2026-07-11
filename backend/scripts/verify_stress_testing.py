import httpx

API_URL = "http://localhost:8000/api/v1"
client = httpx.Client(base_url=API_URL, timeout=10.0)

def main():
    print("--- 1. Fetching Scenarios ---")
    resp = client.get("/stress-scenarios")
    scenarios = resp.json()
    assert len(scenarios) >= 28
    
    # Map by name
    s_map = {s["name"]: s for s in scenarios}
    
    portfolio_id = 1
    
    scenarios_to_test = [
        "RATE_UP_100BP",
        "RATE_DOWN_100BP", 
        "BEAR_STEEPENER", 
        "HY_SPREAD_WIDEN_200BP", 
        "RISK_OFF_SEVERE"
    ]
    
    for s_name in scenarios_to_test:
        print(f"\n--- Running Scenario: {s_name} ---")
        s = s_map[s_name]
        res = client.post(f"/stress-tests/portfolios/{portfolio_id}/run", json={"scenario_id": s["id"]})
        data = res.json()
        
        # Verify sum of positions == portfolio total
        sum_pnl = sum(p["pnl"] for p in data["positions"])
        total_pnl = data["total_pnl"]
        
        diff = abs(sum_pnl - total_pnl)
        print(f"Total PnL: {total_pnl:.2f}, Sum PnL: {sum_pnl:.2f}, Diff: {diff:.5f}")
        assert diff < 1.0, f"PnL mismatch! Diff: {diff}"
        
        if s_name == "HY_SPREAD_WIDEN_200BP":
            for p in data["positions"]:
                if p["rating"] == "AAA" or "Treasury" in p["bond_name"]:
                    print(f"Checking Treasury {p['bond_name']}: Spread Shock = {p['spread_shock_bps']}, PnL = {p['pnl']}")
                    assert p["spread_shock_bps"] == 0
                    assert p["pnl"] == 0
                elif p["rating"] not in ["AAA", "AA", "A", "BBB"] and "Corp" in p["bond_name"]:
                    print(f"Checking HY {p['bond_name']}: Spread Shock = {p['spread_shock_bps']}, PnL = {p['pnl']}")
                    assert p["spread_shock_bps"] == 200
                    assert p["pnl"] < 0
                    
    print("\n--- Compare Scenarios ---")
    s_ids = [s_map[name]["id"] for name in scenarios_to_test]
    res = client.post(f"/stress-tests/portfolios/{portfolio_id}/compare", json={"scenario_ids": s_ids})
    comp_data = res.json()
    scens = comp_data["scenarios"]
    
    print("Ordering:")
    for sc in scens:
        print(f"{sc['scenario_name']}: {sc['total_pnl']}")
        
    for i in range(len(scens)-1):
        assert scens[i]["total_pnl"] <= scens[i+1]["total_pnl"], "Not ordered worst-first"
        
    print("\n--- Retrieve History ---")
    res = client.get(f"/stress-tests/portfolios/{portfolio_id}/history")
    hist = res.json()
    assert len(hist) > 0
    print(f"Found {len(hist)} history runs.")

if __name__ == "__main__":
    main()
