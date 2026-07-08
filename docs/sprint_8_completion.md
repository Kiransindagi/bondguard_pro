# Sprint 8 Completion Report

## 1. Pre-Sprint Defect Investigation
* **Defect Identified**: Market risk models were sporadically evaluating as `NOT_EVALUATED` due to a strict alignment requirement for ETF market data in the `get_historical_var` path. The API incorrectly injected `availability.observation_count` (which reached ~1240 for rate history) into the alignment function, causing `get_aligned_factor_returns` to throw a `RiskEngineError` when ETF context data was slightly shorter (1235 observations).
* **Fix Applied**: Modified `_get_portfolio_and_shocks` in `market_risk.py` to correctly evaluate the underlying requirements against the standard `required_obs` (252) instead of forcing full historical parity on shorter series.

## 2. Database Models
* Created `PortfolioRiskSnapshot` SQLAlchemy model with columns reflecting deterministic risk results (Market Value, Duration, VaR, Breaches, Limits).
* Verified `null` semantics where appropriate.
* Run Alembic migration `ca75d60a98bb (head)` applied to PostgreSQL without failure.

## 3. Snapshot & Executive Reporting Services
* **`SnapshotService`**: Aggregates all previously created authoritative modules without duplicate mathematical engines. Handles idempotent updates natively (same-day regeneration upserts).
* **`Historical Comparison`**: Created `_safe_pct` calculation for deterministic difference over time.
* **`ExecutiveReportService`**: Translates backend data entities into a strict deterministic report model. 

## 4. API Endpoints
* `POST /api/v1/reporting/portfolios/{portfolio_id}/snapshots`
* `GET /api/v1/reporting/portfolios/{portfolio_id}/snapshots`
* `GET /api/v1/reporting/portfolios/{portfolio_id}/executive-report.csv`
* `GET /api/v1/reporting/portfolios/{portfolio_id}/executive-report.pdf` (using `reportlab`)

## 5. Frontend Implementations
* **Overview Page**: Refactored to map strictly to persistent Snapshot variables. Added 4 interactive visual timeline LineCharts (`recharts`).
* **Reporting Page**: Institutional PDF export, CSV export, and snapshot generation functionality fully active. 
* **Risk Intelligence Page**: Added a visual dynamic Production Risk Factor Correlation matrix highlighting structural rate and spread correlations natively via CSS.
* **Build result**: `tsc -b && vite build` succeeded without TS or linter warnings (0 exit code) after correctly managing `recharts` dependencies and correcting `any` type definitions.

## 6. Verification
* PostgreSQL Alembic is at head.
* Live generation created snapshot rows successfully. PDF generated properly with dynamic internal table logic.
* `RATE_ONLY_MODEL` correctly propagates as a governed degradation state without throwing HTTP 500 exceptions.
