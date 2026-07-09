# Developer and AI Agent Guidelines — BondGuard Pro

This document defines the strict engineering standards, mathematical conventions, and architectural constraints for BondGuard Pro. Any human developer or agentic coding assistant must adhere to these guidelines to ensure code quality and consistency.

---

## 1. Financial & Mathematical Conventions

To avoid calculation discrepancies across risk runs, the following conventions are non-negotiable:

### 1.1 Portfolio Accounting
- **Quantity**: Always represents *face-value units* (not number of contracts or rounded quantities).
- **Market Value (MV)**: Calculated as:
  $$MV = Quantity \times FaceValue \times \frac{CleanPrice}{100}$$
- **Unrealized P&L (UP&L)**: Calculated as:
  $$UP\&L = MV - \left(Quantity \times FaceValue \times \frac{AverageCost}{100}\right)$$

### 1.2 Fixed-Income Risk Metrics
- **Parallel Yield Shifts (DV01 / PV01)**: Scaled and reported as a *positive loss magnitude* corresponding to a +1bp upward parallel shift in the yield curve:
  $$DV01 = \frac{Price(y - 1bp) - Price(y + 1bp)}{2}$$
- **Value at Risk (VaR)**: Reported as a *positive loss magnitude* (never negative).
- **Convexity**: Always computed as a positive adjustment factor in second-order Taylor expansion stress approximations.

### 1.3 Market Risk Modeling
- **Returns Sample Minimum**: A strict baseline of **252 observations** of historical daily return factors is required for production VaR calculations.
- **Model Degradation (`RATE_ONLY_MODEL`)**: Under corporate credit-spread history gaps or FRED API ingestion failures, the engine must degrade gracefully to a rate-only model. It maps the interest rate curves while flagging the degradation status (`RATE_ONLY_MODEL`) to the API client instead of failing.

### 1.4 Liquidity Risk Modeling
- **Methodology**: Follows characteristic-based proxy classification (`CHARACTERISTIC_BASED_PROXY_V1`).
- **Concentration**: Measured using the Herfindahl-Hirschman Index (HHI) for issuer and sector exposures.
- **Liquidation Capacity**: Employs capacity degradation shocks based on daily volume constraints.

---

## 2. Risk Limits & Breach Lifecycle

- **Limit Scope Types**: Supports `GLOBAL` limits and `PORTFOLIO` overrides.
- **Breach Status Transitions**:
  - State Machine: `OPEN` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `RESOLVED`.
  - **Deduplication**: When a new limit evaluation run detects a repeated breach, it does *not* create a new breach record. Instead, it updates `observed_value` and `latest_evaluation_run_id` of the existing `OPEN` or `ACKNOWLEDGED` breach.
  - **Reversion Protection**: A breach in an `ACKNOWLEDGED` state must *never* revert to `OPEN` when evaluated again. It remains `ACKNOWLEDGED` until resolved.
- **Audit Logs**: Every breach creation, update, acknowledgement, and resolution must emit an `AuditEvent` with serialization of previous/new states.

---

## 3. Database Isolation & Testing Standards

To prevent thread-locking errors, database pollution, and order-dependent test failures:

### 3.1 Test DB Configurations
- **SQLite Engine**: All pytest suites must run against isolated temporary SQLite files generated outside the workspace (using `tempfile.mkstemp()`).
- **Fixture Usage**:
  - Never override `app.dependency_overrides` at the module or class level.
  - Use function-scoped fixtures `client` (seeded) or `clean_client` (empty database) defined in `conftest.py`.
  - Use `db_session` for unit tests requiring direct database queries.

### 3.2 Frontend Testing (Vitest)
- **Typing Integrity**: Mocks in frontend tests must strictly comply with the Pydantic/TypeScript interfaces defined by the API. Do not bypass or weaken typing properties (e.g. `report.breach_summary` object parameters must always be fully specified).

---

## 4. Coding Style and Linting

- **Backend**: Python code must be checked against `ruff` and strictly format with the black/ruff standard. Do not leave trailing debug prints or untracked DB files.
- **Frontend**: React components must be written using TypeScript, React Query (TanStack), and Tailwind/custom CSS styles, validated by `oxlint` and built with Vite.
