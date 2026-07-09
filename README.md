# BondGuard Pro

Institutional fixed-income portfolio risk analytics platform.

---

## Product Purpose

BondGuard Pro provides real-time and historical risk analytics for fixed-income portfolios, including:
- Deterministic bond pricing (clean price, dirty price, accrued interest, DV01, convexity)
- Historical VaR, Parametric VaR, and Expected Shortfall
- Liquidity risk scoring and HHI concentration analysis
- Stress testing via full revaluation and duration/convexity approximation
- Scenario Lab for user-defined parallel rate and spread shocks
- Advanced analytics: Key Rate Duration (KRD), bucketed DV01, CS01, carry/roll-down, P&L explain
- Risk limit evaluation with breach lifecycle management
- Production data pipeline (FRED API + Yahoo Finance) with data quality gating
- Notification and breach escalation workflows

---

## Architecture Summary

```
BondGuard Pro
├── backend/               FastAPI (Python 3.10+)
│   ├── app/
│   │   ├── api/v1/        REST API endpoints
│   │   ├── auth/          JWT authentication, RBAC, refresh token lifecycle
│   │   ├── data_pipeline/ FRED + yfinance ingestion orchestration
│   │   ├── data_quality/  Dataset freshness and outlier gating
│   │   ├── db/            SQLAlchemy models, Alembic migrations
│   │   ├── notifications/ In-app notification dispatch and deduplication
│   │   ├── reporting/     PDF/CSV executive report generation
│   │   ├── risk_control/  Limit evaluation, breach lifecycle, audit
│   │   ├── risk_engine/   Deterministic pricing, VaR, liquidity, stress
│   │   └── scenario_lab/  User-defined scenario execution and attribution
│   ├── alembic/           Database migration history
│   ├── scripts/           Seed, ingestion, and maintenance scripts
│   └── tests/             Pytest integration and unit tests
└── frontend/              React + TypeScript + Vite
    ├── src/
    │   ├── api/           Typed API client functions
    │   ├── auth/          Auth provider, protected routes, permissions
    │   ├── components/    Shared layout and UI components
    │   └── pages/         One page per domain module
    └── src/test/          Vitest component tests
```

---

## Technology Stack

| Layer        | Technology                                |
|-------------|-------------------------------------------|
| Backend API  | FastAPI, SQLAlchemy, Pydantic v2, Alembic |
| Database     | PostgreSQL (production), SQLite (tests)   |
| Auth         | JWT (access + refresh tokens), bcrypt     |
| Risk Engine  | NumPy, pandas, scipy                      |
| Data Sources | FRED API, Yahoo Finance (yfinance)        |
| Frontend     | React 18, TypeScript, Vite, TanStack Query|
| Charts       | Plotly.js (react-plotly.js)               |
| Testing      | Pytest (backend), Vitest (frontend)       |
| Linting      | Ruff (backend), oxlint (frontend)         |
| Containers   | Docker Compose                            |

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+ (production) or SQLite (tests only)

---

## Environment Setup

```bash
cp .env.example .env        # Edit DATABASE_URL and FRED_API_KEY
cp .env.example backend/.env
```

Required `.env` variables:
```
DATABASE_URL=postgresql://user:password@localhost:5432/bondguard_db
FRED_API_KEY=your_key_here
JWT_SECRET_KEY=your_secret_key_here
ENVIRONMENT=development
```

---

## Migrations

```bash
cd backend
python -m alembic upgrade head    # Apply all migrations
python -m alembic current          # Verify current migration head
python -m alembic history          # View full migration chain
```

---

## Seed Commands

Run from `backend/`:
```bash
python -m scripts.seed.seed_roles_permissions
python -m scripts.seed.seed_portfolio
python -m scripts.seed.seed_stress_scenarios
python -m scripts.seed.seed_liquidity_assumptions
python -m scripts.seed.seed_concentration_limits
python -m scripts.seed.seed_risk_limits
```

---

## Backend Startup

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate         # Windows
# source venv/bin/activate      # Linux/macOS
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/api/v1/openapi.json`

---

## Frontend Startup

```bash
cd frontend
npm install
npm run dev           # Dev server on http://localhost:5173
```

---

## Tests

**Backend:**
```bash
cd backend
$env:PYTHONPATH="."             # Windows PowerShell
python -m pytest -v
python -m ruff check .
```

**Frontend:**
```bash
cd frontend
npm run test -- --run
npm run build
```

---

## Docker Startup

```bash
docker compose up --build
```

Services: `api` (port 8000), `frontend` (port 5173), `db` (PostgreSQL port 5432).

---

## Known Model Limitations

- **Rate-Only Model Degradation (`RATE_ONLY_MODEL`)**: When credit spread history fails data quality gates or the FRED API is unavailable, the VaR engine degrades gracefully to rate factors only. The API response includes `model_status: RATE_ONLY_MODEL`. This is by design and is clearly flagged in the frontend.
- **Minimum Observations**: Production VaR requires a minimum of 252 trading days of factor history. Risk runs below this threshold are blocked at the data quality gate.
- **Spread Duration (CS01)**: Treasuries have zero spread sensitivity by construction. CS01 is only non-zero for `bond_type == "Corporate"`.
- **P&L Explain**: The `residual` component captures pricing model differences and is expected to be non-zero. It is not an error condition.
- **Carry and Roll-Down**: Based on deterministic yield curve interpolation at shifted maturities. Does not account for stochastic rate dynamics.

---

## Documentation Index

| Topic | Location |
|-------|----------|
| System Architecture | `docs/architecture/system_architecture.md` |
| Data Sources | `docs/architecture/data_sources.md` |
| Reporting Architecture | `docs/architecture/reporting_architecture.md` |
| Portfolio Engine | `docs/domain/portfolio_engine.md` |
| Risk Engine | `docs/domain/risk_engine.md` |
| Stress Testing | `docs/domain/stress_testing.md` |
| Reporting Contract | `docs/domain/reporting_contract.md` |
| Breach Management | `docs/operations/breach_management.md` |
| Risk Control | `docs/operations/risk_control.md` |
| Risk Snapshots | `docs/operations/risk_snapshots.md` |
| Development Standards | `docs/governance/development.md` |
| AI Agent Guidelines | `AGENTS.md` |
