# Sprint 5: Institutional Stress Testing & Scenario Analysis

## Overview
The Institutional Stress Testing & Scenario Analysis module allows users to apply macroscopic parallel and non-parallel shocks across Treasury yield curves and Credit Spread curves to identify vulnerabilities within the portfolio.

## Implementation Status
- **Database Schema**: Successfully created schemas for `stress_scenarios`, `stress_test_runs`, and `stress_position_results` utilizing Alembic for PostgreSQL migrations.
- **Service Layer**:
  - `scenario_pricing.py`: Manages evaluation of Bond P&L based on `FULL_REVALUATION` (repricing bonds precisely using cashflow scheduling) and `APPROXIMATION` calculations.
  - `scenario_runner.py`: Responsible for evaluating portfolios against stress profiles, computing P&L per position.
  - `portfolio_stress.py`: Evaluates and compares top scenarios efficiently for comprehensive portfolio stress analysis.
- **Predefined Shocks**: Idempotent script `seed_stress_scenarios.py` successfully implemented to seed baseline profiles including:
  - Parallel Shocks (`RATE_UP_100BP`)
  - Steepeners / Flatteners (`BEAR_STEEPENER`)
  - Credit Shocks (`HY_SPREAD_WIDEN_500BP`)
  - Combined Risk Scenarios (`CREDIT_CRISIS`)
- **API Endpoints**: 
  - FastAPI routers integrated to handle CRUD operations on `stress-scenarios`.
  - Portfolio Execution endpoint at `/api/v1/stress-tests/portfolios/{portfolio_id}/run`.
  - Portfolio Comparison endpoint at `/api/v1/stress-tests/portfolios/{portfolio_id}/compare`.
- **Frontend Dashboard**: Fully interactive React application under `/stress-testing`. It incorporates modern UI patterns with Lucide icons without unnecessary bloat, supporting:
  - Scenario Execution and Live Analytics.
  - Deep Position P&L Attribution Breakdowns.
  - Scenario Comparison.

## Verification
- Backend tests have been verified with `pytest tests/test_stress_testing.py` and across the larger test suite (64/64 passing).
- React components have been verified via Vitest tests passing correctly. Production bundles successfully build via `npm run build`.

## Next Steps
- Consider further enriching the Stress Scenario visualization with yield curve visual shifts (Before/After) once further plotting libraries (e.g., Plotly) are integrated on the UI.
