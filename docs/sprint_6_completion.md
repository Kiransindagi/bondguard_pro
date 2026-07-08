# Sprint 6 — Liquidity Risk & Concentration Analytics Completion

## 1. Migration & Table Inspection
- **Migration Head**: Confirmed `12c458666f1b` is the current head using `alembic current`.
- **Row Counts**: Seed scripts (`seed_liquidity_assumptions.py` and `seed_concentration_limits.py`) are strictly idempotent. Re-running them proves row counts remain stable (1 assumption, 6 active limits) with no duplication bloat.

## 2. Concentration Persistence Strategy
Concentration results are currently calculated dynamically on demand (via `/api/v1/liquidity-risk/portfolios/{portfolio_id}/concentration?dimension=...`) and not persisted statically into `ConcentrationSnapshot`. 
- **Reasoning**: This on-the-fly approach leverages live PostgreSQL queries to compute precise HHI and bucket weights efficiently across 6+ different dimension types without generating unnecessary `ConcentrationSnapshot` table bloat (which would require persisting 6+ permutations for every single daily snapshot).
- **Extensibility**: The API structure allows concentration snapshots to be fully persisted historically at a later date if regulatory point-in-time auditing of concentration requires it without breaking the API schema.

## 3. PostgreSQL Live Endpoints & Reconciliation
The Liquidity service gracefully executed all analytical requirements over the `Global Core Fixed Income` portfolio:
- **Weighted Liquidity Score**: 73.85 (0-100 scale)
- **Total Estimated Liquidation Cost**: $3,083.75 (11.91 bps)
- **Weighted Days-to-Liquidate**: 1.36 days
- **Maximum Days-to-Liquidate**: 4 days
- **Very Low Liquidity Weight**: 0.0% (No "VERY_LOW" assets in the portfolio)
- **Concentration Bounds**: Treasury asserts a 38.43% weight, fitting comfortably within configured concentration thresholds. The exact breakdown correctly scales to 1.0 (100%).
- **Reconciliation**:
  - `sum(position_liquidation_costs) == portfolio_liquidation_cost` ($3,083.75)
  - `sum(concentration_weights) == 1.0` (100% of the portfolio). Zero-market-value bonds accurately drop to a `0.0` weight.

## 4. Liquidity Stress Testing
Stress tests correctly model a degradation in both capacity (prolonging the time-to-liquidate) and bid-ask spreads (increasing cost):
- **Normal Cost**: $3,083.75 (1.36 Days)
- **Moderate Stress**: $4,625.62 (2.04 Days)
- **Severe Stress**: $7,709.37 (3.40 Days)
Cost monotonically increases (Severe > Moderate > Normal) and days-to-liquidate deteriorate proportionally to configured capacity shocks.

## 5. API Labeling & Model Limitations
- The API explicitly returns properties `methodology = "CHARACTERISTIC_BASED_PROXY_V1"` and `limitations = "Model estimates based on characteristics proxy. Does not reflect real individual ADV."` to ensure end-users understand that capacity estimates are synthetic proxies rather than observed tick data.
- The **Liquidity-Adjusted VaR** explicitly exposes `market_risk_model_status = "RATE_ONLY_MODEL"` and highlights that missing credit-spread history compromises the underlying Market VaR, preventing the illusion that the liquidity-adjustment "fixes" missing historical factor data.

## 6. Regression Expansion
Expanded Pytest suites in `backend/tests/test_liquidity_risk.py` verify HHI math, zero-market-value behavior, top-N concentration, and atomic scenario bounds, bringing the active suite count to 18 liquidity tests specifically, contributing heavily to the comprehensive 110-test objective.
