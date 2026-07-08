# BondGuard Pro

Institutional fixed-income portfolio risk analytics platform.

## Architecture

BondGuard Pro uses a FastAPI backend and a React (TypeScript, Vite) frontend.

## Quickstart

### Prerequisites
- Python 3.12
- Node.js
- PostgreSQL

### Database setup
Create a local database named `bondguard_db`.
Copy `.env.example` to `.env` in the root folder, and also into `backend/.env`. Fill in `FRED_API_KEY` and the correct `DATABASE_URL`.

### Backend
1. `cd backend`
2. `pip install -r requirements.txt`
3. Run migrations: `alembic upgrade head`
4. Seed Sprint 2 Portfolio Data: `python seed_portfolio.py`
5. Start the API: `python -m uvicorn app.main:app --reload`
6. Run tests: `python -m pytest -v`

### Frontend
1. `cd frontend`
2. `npm install`
3. Start the dev server: `npm run dev`
4. Run tests: `npm run test`
5. Run production build: `npm run build`

## Features
- **Sprint 1**: Market data ingestion pipeline (FRED, yfinance).
- **Sprint 2**: Institutional Portfolio and Position management, accounting rules, and WAC tracking. Includes a React dashboard.
- **Sprint 3 (Risk Engine)**: 
  - Pure numerical fixed-income valuation from discounted cash flows.
  - Custom Yield-to-Maturity (YTM) bisection solver.
  - Duration (Macaulay/Modified) and Convexity calculations.
  - DV01 via finite difference and quantity scaling.
  - Yield Curve Interpolation (Linear interpolation with flat extrapolation).
  - Risk API endpoints mapping portfolio risks securely.

*Note: Historical VaR, Parametric VaR, Stress Testing, and Machine Learning algorithms are NOT yet implemented.*

## Risk API Endpoints Example

*   `GET /api/v1/risk/bonds/{bond_id}?clean_price=99.5`
*   `GET /api/v1/risk/portfolios/{portfolio_id}/summary`
*   `GET /api/v1/risk/portfolios/{portfolio_id}/positions`
*   `GET /api/v1/risk/curve`
