# Architecture

BondGuard Pro is a full-stack web application designed for fixed-income portfolio risk analytics.

## Backend
- Python 3.12, FastAPI, SQLAlchemy 2.x
- PostgreSQL database
- Alembic for database migrations

## Frontend
- React 18+ with TypeScript
- Vite bundler
- TanStack Query for data fetching
- React Router for client-side navigation
- Plotly for financial visualizations (planned)

## Deployment
- Docker containerization for all components
- GitHub Actions CI for running tests and builds
