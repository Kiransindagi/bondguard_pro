# Sprint 7 & 7.1 Completion Report

## 1. Files Created/Modified
* **Modified**: `backend/app/risk_control/adapters/liquidity_risk.py` (fixed field name to match model).
* **Modified**: `frontend/src/pages/RiskIntelligence.tsx` (null coalescing).
* **Created**: `backend/tests/test_risk_control_lifecycle.py` (test suite for evaluation, limit precedence, boundary conditions).
* **Created**: Documentation (`docs/risk_control.md`, `docs/breach_management.md`, `docs/sprint_7_completion.md`).

## 2. Migration and Seeding
* Alembic is up to date (`fe426ade3873 (head)`).
* `seed_risk_limits.py` executed successfully twice, demonstrating full idempotency.
* 9 active seeded limits correctly mapped and verified.

## 3. Metric Adapter Reconciliation
All active seeded limits accurately map to their metric adapters:
* `PORTFOLIO_MODIFIED_DURATION` -> deterministic adapter (years)
* `TOTAL_DV01` -> deterministic adapter (USD)
* `HISTORICAL_VAR_95_1D` -> market risk adapter (USD)
* `WORST_STRESS_LOSS` -> stress risk adapter (USD)
* `ISSUER_CONCENTRATION_MAX` -> concentration adapter (ratio)
* `SECTOR_CONCENTRATION_MAX` -> concentration adapter (ratio)
* `LIQUIDITY_SCORE` -> liquidity adapter (score)
* `LIQUIDATION_COST_BPS` -> liquidity adapter (bps)
* `MAX_DAYS_TO_LIQUIDATE` -> liquidity adapter (days)

## 4. Testing Results
* Backend Tests: Executed limit precedence, boundary (MIN/MAX) testing, first breach, repeat deduplication, acknowledgment, recovery, and re-breach paths via Pytest. 
* Frontend Tests: 25 tests across 8 suites executed successfully (including rendering logic for PASS/WARNING/BREACH/NOT_EVALUATED).
* Frontend Build: 1898 modules built successfully in ~7 seconds without TypeScript errors.

## 5. Live Verification
Tested directly against PostgreSQL:
* Evaluation of Portfolio 1 created Run #12.
* Deduplicated breach updates verified (no duplicate OPEN breaches).
* `NOT_EVALUATED` behavior verified gracefully (e.g. VaR failure due to lack of historical history returns HTTP 200 with limitation info instead of HTTP 500).
* Audit event API correctly returns append-only `BREACH_UPDATED` and `EVALUATION_COMPLETED` events.
* Acknowledgment persists correctly (`status: ACKNOWLEDGED`).

## 6. Known Limitations & Technical Debt
* Liquidity metrics are calculated using characteristic proxies, not real executed tick data.
* Market risk models lack historical history in development environments and purposefully degrade gracefully.
* Currently limited to Portfolio and Global limit overrides (security-level limits not yet evaluated).
