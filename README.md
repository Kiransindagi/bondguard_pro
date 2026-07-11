# BondGuard Pro

> **Integrated Fixed-Income Portfolio Risk Analytics Platform**

BondGuard Pro is a full-stack fixed-income portfolio risk analytics platform that integrates market-data ingestion, deterministic bond valuation, portfolio risk measurement, stress testing, scenario analysis, liquidity and concentration analytics, risk-limit monitoring, breach management, notifications, historical risk snapshots, and executive reporting.

The project is designed around a complete risk-management workflow:

```text
Market Data
    ↓
Data Quality Validation
    ↓
Portfolio Valuation
    ↓
Risk Analytics
    ↓
Stress Testing & Scenario Analysis
    ↓
Risk Limit Evaluation
    ↓
Breach Management
    ↓
Notifications
    ↓
Historical Snapshots
    ↓
Executive Reporting
```

Unlike a notebook-based finance project or dashboard-only application, BondGuard Pro connects quantitative analytics with backend services, production-style data pipelines, model governance, security controls, operational workflows, persistent storage, automated testing, and a typed analytical frontend.

---

## Table of Contents

* [Product Overview](#product-overview)
* [Core Capabilities](#core-capabilities)
* [System Architecture](#system-architecture)
* [End-to-End Platform Flow](#end-to-end-platform-flow)
* [Risk Analytics Architecture](#risk-analytics-architecture)
* [Market Data Pipeline](#market-data-pipeline)
* [Data Quality Gate](#data-quality-gate)
* [Risk Control Architecture](#risk-control-architecture)
* [Authentication and Authorization](#authentication-and-authorization)
* [Technology Stack](#technology-stack)
* [Repository Structure](#repository-structure)
* [Project Benchmark](#project-benchmark)
* [Engineering Highlights](#engineering-highlights)
* [API Architecture](#api-architecture)
* [Database Architecture](#database-architecture)
* [Installation](#installation)
* [Environment Configuration](#environment-configuration)
* [Database Migrations](#database-migrations)
* [Seed Data](#seed-data)
* [Running the Application](#running-the-application)
* [Docker](#docker)
* [Testing and Quality Gates](#testing-and-quality-gates)
* [Model Governance](#model-governance)
* [Known Model Limitations](#known-model-limitations)
* [Production Considerations](#production-considerations)
* [Screenshots and Demo](#screenshots-and-demo)
* [Documentation](#documentation)
* [Roadmap](#roadmap)
* [Project Maturity](#project-maturity)

---

# Product Overview

Institutional fixed-income risk management requires more than bond pricing.

A complete analytical system needs to answer questions such as:

* What is the current market value of the portfolio?
* What is the clean and dirty price of each security?
* How much accrued interest has accumulated?
* How sensitive is the portfolio to a one-basis-point rate movement?
* Where is duration concentrated across the yield curve?
* What is the portfolio's potential loss under historical market conditions?
* What is the Expected Shortfall beyond the VaR threshold?
* How does the portfolio behave under severe rate and spread shocks?
* Which issuers and sectors dominate concentration?
* How quickly can positions be liquidated under stressed market conditions?
* Which risk limits have been breached?
* Who acknowledged or resolved a breach?
* Is market data sufficiently fresh and complete for model execution?
* Can the model degrade safely when credit-spread history becomes unavailable?
* Can historical risk states be reconstructed and audited?

BondGuard Pro is structured around these questions.

The platform separates the following responsibilities:

1. Market-data ingestion
2. Data normalization
3. Data-quality validation
4. Portfolio valuation
5. Risk-factor construction
6. Risk calculation
7. Stress testing
8. Scenario execution
9. Risk-limit evaluation
10. Breach lifecycle management
11. Notification dispatch
12. Historical snapshot persistence
13. Executive reporting
14. Frontend visualization

---

# Core Capabilities

## Fixed-Income Valuation

The deterministic pricing engine supports:

* Clean price
* Dirty price
* Accrued interest
* Yield-based bond valuation
* Macaulay duration
* Modified duration
* DV01
* Convexity
* Unrealized P&L
* Position-level market value
* Portfolio-level valuation aggregation

The pricing layer is intentionally deterministic so risk calculations, stress tests, scenario attribution, and reports can be reproduced consistently.

### Valuation Flow

```text
Bond Terms
    +
Yield / Curve Data
    ↓
Cash Flow Schedule
    ↓
Discounting Engine
    ↓
┌─────────────────────┐
│ Clean Price         │
│ Dirty Price         │
│ Accrued Interest    │
│ Duration            │
│ DV01                │
│ Convexity           │
└─────────────────────┘
```

---

## Market Risk

BondGuard Pro supports:

* Historical VaR
* Parametric VaR
* Expected Shortfall
* Configurable confidence levels
* Configurable holding periods
* Rate-factor modeling
* Credit-spread factor modeling
* Explicit rate-only degraded model operation
* Minimum observation enforcement
* Portfolio-level risk aggregation

Production VaR requires a minimum of:

```text
252 trading-day observations
```

Risk runs below the required observation threshold are blocked by the data-quality gate.

---

## Interest Rate Risk

Interest-rate analytics include:

* Portfolio DV01
* Bond-level DV01
* Key Rate Duration
* Bucketed DV01
* Parallel rate shocks
* Non-parallel yield-curve shocks
* Duration/convexity approximation
* Full revaluation

Key-rate analytics allow the system to identify where portfolio interest-rate exposure is concentrated across different maturity segments of the curve.

---

## Credit Spread Risk

Credit analytics include:

* CS01
* Spread shock scenarios
* Corporate bond spread sensitivity
* Spread contribution to stress P&L
* Credit-spread factor integration in VaR models

Treasury securities have zero spread sensitivity by construction.

```text
CS01 = 0 when bond_type != "Corporate"
```

---

## Stress Testing

The stress engine supports:

* Full bond revaluation
* Duration/convexity approximation
* Parallel interest-rate shocks
* Yield-curve shocks
* Credit-spread widening
* Combined rate and spread scenarios
* Position-level contribution
* Portfolio-level aggregation
* Scenario comparison

### Stress Execution Flow

```text
Stress Scenario
       ↓
Scenario Validation
       ↓
Portfolio Position Load
       ↓
Shock Application
       │
       ├── Rate Shock
       ├── Curve Shock
       └── Spread Shock
       ↓
Bond Revaluation
       ↓
Position P&L
       ↓
Portfolio Aggregation
       ↓
Persisted Stress Result
```

---

## Scenario Lab

The Scenario Lab allows analysts to define custom combinations of:

* Parallel interest-rate shocks
* Credit-spread shocks
* Portfolio-specific assumptions

### Scenario Lab Flow

```text
User Scenario
      ↓
Scenario Validation
      ↓
Portfolio Load
      ↓
Shock Application
      │
      ├── Rate Shock
      └── Spread Shock
      ↓
Bond Revaluation
      ↓
Position-Level Attribution
      ↓
Portfolio Aggregation
      ↓
Persisted Scenario Result
```

---

## Liquidity Risk

Liquidity analytics include:

* Liquidity scoring
* Position liquidation estimates
* Market-capacity assumptions
* Stressed liquidity degradation
* Concentration-adjusted liquidity analysis

The system supports configurable liquidity assumptions so different bond categories can be evaluated using different market-capacity profiles.

---

## Concentration Risk

Portfolio concentration is measured using:

* Issuer concentration
* Sector concentration
* Herfindahl-Hirschman Index
* Configurable concentration limits
* Concentration breach detection

This connects descriptive portfolio analytics with the risk-control framework.

---

## Advanced Analytics

BondGuard Pro includes:

* Key Rate Duration
* Bucketed DV01
* CS01
* Carry analysis
* Roll-down analysis
* P&L Explain

### P&L Explain

```text
Total P&L
   │
   ├── Carry
   ├── Roll-Down
   ├── Rate Effect
   ├── Spread Effect
   └── Residual
```

The residual component captures pricing and model differences that are not fully explained by the analytical decomposition.

A non-zero residual is not automatically an error condition.

---

# System Architecture

```mermaid
flowchart TB
    subgraph CLIENT["Client Layer"]
        UI["React + TypeScript"]
        QUERY["TanStack Query"]
        CHARTS["Plotly Analytics"]
    end

    subgraph API["API Layer"]
        FASTAPI["FastAPI REST API"]
        AUTH["Authentication & RBAC"]
    end

    subgraph DOMAIN["Domain Services"]
        PORT["Portfolio Engine"]
        RISK["Risk Engine"]
        STRESS["Stress Engine"]
        SCENARIO["Scenario Lab"]
        CONTROL["Risk Control"]
        REPORT["Reporting"]
        NOTIFY["Notifications"]
    end

    subgraph DATA["Data Platform"]
        FRED["FRED API"]
        YAHOO["Yahoo Finance"]
        PIPE["Ingestion Pipeline"]
        DQ["Data Quality Gate"]
    end

    subgraph STORAGE["Persistence"]
        DB[("PostgreSQL")]
        MIG["Alembic Migrations"]
    end

    UI --> QUERY
    QUERY --> FASTAPI
    CHARTS --> UI

    FASTAPI --> AUTH
    FASTAPI --> PORT
    FASTAPI --> RISK
    FASTAPI --> STRESS
    FASTAPI --> SCENARIO
    FASTAPI --> CONTROL
    FASTAPI --> REPORT

    FRED --> PIPE
    YAHOO --> PIPE
    PIPE --> DQ
    DQ --> RISK

    PORT --> DB
    RISK --> DB
    STRESS --> DB
    SCENARIO --> DB
    CONTROL --> DB
    REPORT --> DB
    NOTIFY --> DB

    CONTROL --> NOTIFY
    MIG --> DB
```

---

# End-to-End Platform Flow

```mermaid
flowchart TD
    A["External Market Data"] --> B["Ingestion Pipeline"]
    B --> C["Normalization"]
    C --> D["Data Quality Gate"]

    D -->|"Rate + Spread Valid"| E["FULL_FACTOR_MODEL"]
    D -->|"Spread Degraded"| F["RATE_ONLY_MODEL"]
    D -->|"Core Data Insufficient"| G["Risk Run Blocked"]

    E --> H["Portfolio Valuation"]
    F --> H

    H --> I["Risk Analytics"]

    I --> J["VaR & Expected Shortfall"]
    I --> K["DV01 / KRD / CS01"]
    I --> L["Liquidity Risk"]
    I --> M["Concentration Risk"]
    I --> N["Stress Testing"]
    I --> O["Scenario Lab"]

    J --> P["Risk Limit Engine"]
    K --> P
    L --> P
    M --> P
    N --> P
    O --> P

    P --> Q["Breach Detection"]
    Q --> R["Breach Lifecycle"]
    R --> S["Notifications"]
    S --> T["Historical Risk Snapshots"]
    T --> U["Executive Reporting"]
    U --> V["React Analytics Dashboard"]
```

---

# Risk Analytics Architecture

```text
Portfolio
    ↓
Positions
    │
    ├── Bond Terms
    ├── Quantity
    ├── Cost Basis
    └── Market Value
    ↓
Pricing Engine
    │
    ├── Clean Price
    ├── Dirty Price
    ├── Accrued Interest
    ├── Duration
    ├── DV01
    └── Convexity
    ↓
Portfolio Risk Engine
    │
    ├── Historical VaR
    ├── Parametric VaR
    ├── Expected Shortfall
    ├── Key Rate Duration
    ├── Bucketed DV01
    ├── CS01
    ├── Liquidity Risk
    └── Concentration Risk
    ↓
Stress & Scenario Layer
    ↓
Risk Limit Evaluation
    ↓
Breach Workflow
    ↓
Snapshots & Reports
```

---

# Market Data Pipeline

BondGuard Pro uses a controlled ingestion architecture instead of allowing analytical models to consume external API responses directly.

```mermaid
flowchart LR
    F["FRED API"] --> I["Ingestion"]
    Y["Yahoo Finance"] --> I

    I --> N["Normalization"]
    N --> P["Persistence"]
    P --> Q["Data Quality Gate"]
    Q --> R["Risk Factor Construction"]
    R --> M["Risk Models"]
```

## Treasury Rates

Supported Treasury series include:

* DGS2
* DGS5
* DGS10
* DGS30

## Credit Spread Data

The data pipeline supports:

* Investment-grade spread history
* High-yield spread history

## Macro Data

The macro pipeline includes:

* Federal Funds Effective Rate

## Fixed-Income ETF Data

The ingestion architecture supports ETF market data representing:

* Short-duration Treasuries
* Intermediate-duration Treasuries
* Long-duration Treasuries
* Investment-grade credit
* High-yield credit
* Emerging-market debt

---

# Data Quality Gate

No production risk calculation should silently operate on invalid or insufficient market data.

The data-quality gate evaluates:

* Dataset freshness
* Observation count
* Required columns
* Missing values
* Outlier conditions
* Credit-spread availability
* Core rate-factor availability

### Decision Flow

```mermaid
flowchart TD
    A["Dataset"] --> B{"Fresh?"}
    B -->|No| X["Reject / Degrade"]
    B -->|Yes| C{"Enough Observations?"}

    C -->|No| Y["Block Production Risk Run"]
    C -->|Yes| D{"Required Fields Present?"}

    D -->|No| X
    D -->|Yes| E{"Outlier Check Pass?"}

    E -->|No| X
    E -->|Yes| F{"Credit Factors Valid?"}

    F -->|Yes| G["FULL_FACTOR_MODEL"]
    F -->|No| H["RATE_ONLY_MODEL"]
```

Production VaR requires:

```text
minimum_observations = 252
```

If rate data remains valid while credit-spread data fails validation, the system may explicitly degrade to:

```text
RATE_ONLY_MODEL
```

The degraded state is returned through the API and surfaced in the frontend.

---

# Risk Control Architecture

Risk analytics become operationally useful when measurement is connected to governance workflows.

```mermaid
flowchart TD
    A["Risk Calculation"] --> B["Limit Evaluation"]
    B --> C{"Limit Breached?"}

    C -->|No| D["Record Evaluation"]
    C -->|Yes| E["Deduplication Check"]

    E --> F{"Existing Active Breach?"}
    F -->|Yes| G["Update Existing Workflow"]
    F -->|No| H["Create Breach"]

    H --> I["OPEN"]
    I --> J["ACKNOWLEDGED"]
    J --> K["RESOLVED"]

    I --> L["Audit History"]
    J --> L
    K --> L

    H --> M["Notification Dispatch"]
```

The risk-control layer supports:

* Configurable limits
* Automated evaluation
* Breach creation
* Duplicate breach prevention
* Acknowledgement workflows
* Resolution workflows
* User attribution
* Timestamps
* Audit history
* Notification dispatch

---

# Authentication and Authorization

BondGuard Pro implements:

* JWT access tokens
* Refresh token lifecycle
* bcrypt password hashing
* Protected API routes
* Protected frontend routes
* Role-based access control
* Permission-aware UI behavior

### Role Hierarchy

```text
Reader
   ↓
Analyst
   ↓
Manager
   ↓
Admin
```

| Role    | Primary Access                                                |
| ------- | ------------------------------------------------------------- |
| Reader  | View dashboards, portfolios, reports, and risk results        |
| Analyst | Run analytics, stress tests, and custom scenarios             |
| Manager | Manage risk controls and breach workflows                     |
| Admin   | Manage users, roles, permissions, and platform administration |

Authorization is enforced at the backend API layer.

Frontend route protection is treated as a usability layer, not as the primary security boundary.

---

# Technology Stack

| Layer               | Technology           |
| ------------------- | -------------------- |
| Backend API         | FastAPI              |
| Backend Language    | Python 3.10+         |
| ORM                 | SQLAlchemy           |
| Validation          | Pydantic v2          |
| Database Migration  | Alembic              |
| Production Database | PostgreSQL           |
| Test Database       | Isolated SQLite      |
| Authentication      | JWT + bcrypt         |
| Risk Analytics      | NumPy, pandas, scipy |
| Market Data         | FRED API, yfinance   |
| Frontend            | React 18             |
| Frontend Language   | TypeScript           |
| Build Tool          | Vite                 |
| Server State        | TanStack Query       |
| Visualization       | Plotly.js            |
| Backend Testing     | Pytest               |
| Frontend Testing    | Vitest               |
| Backend Linting     | Ruff                 |
| Frontend Linting    | oxlint               |
| Containers          | Docker Compose       |
| Reporting           | ReportLab + CSV      |

---

# Repository Structure

```text
bondguard-pro/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       └── REST API endpoints
│   │   │
│   │   ├── auth/
│   │   │   ├── authentication
│   │   │   ├── JWT lifecycle
│   │   │   ├── RBAC
│   │   │   └── permissions
│   │   │
│   │   ├── data_pipeline/
│   │   │   ├── FRED ingestion
│   │   │   ├── market-data ingestion
│   │   │   └── orchestration
│   │   │
│   │   ├── data_quality/
│   │   │   ├── freshness checks
│   │   │   ├── observation validation
│   │   │   └── outlier detection
│   │   │
│   │   ├── db/
│   │   │   ├── models
│   │   │   ├── sessions
│   │   │   └── persistence
│   │   │
│   │   ├── notifications/
│   │   │   ├── dispatch
│   │   │   └── deduplication
│   │   │
│   │   ├── reporting/
│   │   │   ├── PDF reports
│   │   │   └── CSV exports
│   │   │
│   │   ├── risk_control/
│   │   │   ├── limits
│   │   │   ├── breaches
│   │   │   └── audit workflows
│   │   │
│   │   ├── risk_engine/
│   │   │   ├── bond pricing
│   │   │   ├── VaR
│   │   │   ├── Expected Shortfall
│   │   │   ├── liquidity
│   │   │   ├── concentration
│   │   │   ├── stress testing
│   │   │   └── advanced analytics
│   │   │
│   │   └── scenario_lab/
│   │       ├── scenario definitions
│   │       ├── execution
│   │       └── attribution
│   │
│   ├── alembic/
│   ├── scripts/
│   │   ├── seed/
│   │   ├── ingestion/
│   │   └── maintenance/
│   │
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── components/
│   │   ├── pages/
│   │   └── test/
│   │
│   └── public/
│
├── docs/
│   ├── architecture/
│   ├── domain/
│   ├── governance/
│   └── operations/
│
├── .github/
│   └── workflows/
│
├── docker-compose.yml
├── .env.example
├── AGENTS.md
└── README.md
```

---

# Project Benchmark

BondGuard Pro is designed beyond the scope of a typical academic finance dashboard, CRUD application, notebook-based VaR model, or isolated machine-learning project.

The following comparison is a scope benchmark, not an external industry ranking.

| Capability                        | Typical Student Finance Project | Strong Portfolio Project |              BondGuard Pro |
| --------------------------------- | ------------------------------: | -----------------------: | -------------------------: |
| Bond Pricing                      |                           Basic |                      Yes |                        Yes |
| Accrued Interest                  |                            Rare |                Sometimes |                        Yes |
| Duration & Convexity              |                       Sometimes |                      Yes |                        Yes |
| DV01                              |                            Rare |                      Yes |                        Yes |
| Historical VaR                    |                           Basic |                      Yes |                        Yes |
| Parametric VaR                    |                            Rare |                Sometimes |                        Yes |
| Expected Shortfall                |                            Rare |                Sometimes |                        Yes |
| Key Rate Duration                 |                       Very Rare |                     Rare |                        Yes |
| Bucketed DV01                     |                       Very Rare |                     Rare |                        Yes |
| CS01                              |                       Very Rare |                     Rare |                        Yes |
| Liquidity Risk                    |                            Rare |                Sometimes |                        Yes |
| HHI Concentration                 |                       Sometimes |                      Yes |                        Yes |
| Full-Revaluation Stress Testing   |                            Rare |                     Rare |                        Yes |
| Custom Scenario Lab               |                            Rare |                     Rare |                        Yes |
| Carry & Roll-Down                 |                       Very Rare |                     Rare |                        Yes |
| P&L Explain                       |                       Very Rare |                     Rare |                        Yes |
| Production Data Pipeline          |              Usually Manual CSV |                Basic API |       FRED + Yahoo Finance |
| Data Quality Gate                 |                 Usually Missing |         Basic Validation |   Multi-Stage Quality Gate |
| Explicit Model Degradation        |                 Usually Missing |                     Rare |          `RATE_ONLY_MODEL` |
| Minimum Model History Enforcement |                 Usually Missing |                Sometimes |           252 Observations |
| Risk Limit Engine                 |                 Usually Missing |                     Rare |                        Yes |
| Breach Lifecycle                  |                 Usually Missing |                     Rare |                        Yes |
| Notification Deduplication        |                 Usually Missing |                     Rare |                        Yes |
| Historical Risk Snapshots         |                            Rare |                Sometimes |                        Yes |
| Executive Reporting               |                    Basic Export |                Sometimes |                  PDF + CSV |
| Authentication                    |                     Basic Login |                      JWT | Access + Refresh Lifecycle |
| RBAC                              |                 Usually Missing |              Basic Roles |         4-Level Role Model |
| Database Migrations               |                   Often Missing |                      Yes |            Alembic History |
| Backend Automated Tests           |                         Limited |                 Moderate |                153 Passing |
| Frontend Automated Tests          |                   Often Missing |                  Limited |                 25 Passing |
| Type Safety                       |                       Sometimes |                      Yes |        0 TypeScript Errors |
| Containerization                  |                       Sometimes |                      Yes |  Full-Stack Docker Compose |

---

## Engineering Scale

Current verified benchmark:

```text
Backend Tests                 153 / 153 passing
Frontend Tests                 25 / 25 passing
Total Automated Tests         178 passing
TypeScript Errors               0
Production VaR Minimum        252 observations

Backend Architecture          Modular domain architecture
API Architecture              Versioned REST API
Production Database           PostgreSQL
Test Isolation                Isolated SQLite databases

Authentication                JWT access + refresh lifecycle
Authorization                 Role-based access control
Reporting                     PDF + CSV
Deployment Model              Docker Compose
```

These numbers should be updated whenever the repository changes so the README remains synchronized with the actual implementation.

---

## Maturity Assessment

| Dimension            | Demonstrated Capability                            | Assessment               |
| -------------------- | -------------------------------------------------- | ------------------------ |
| Quantitative Finance | Pricing, VaR, ES, sensitivities, stress, liquidity | Advanced Portfolio Scope |
| Backend Engineering  | Modular APIs, services, persistence, migrations    | Strong                   |
| Data Engineering     | Ingestion, normalization, quality gating           | Strong                   |
| Frontend Engineering | Typed React analytical application                 | Strong                   |
| Security             | JWT lifecycle, RBAC, protected routes              | Strong Portfolio Scope   |
| Quality Engineering  | Backend, frontend, integration, and domain tests   | Strong                   |
| Operational Workflow | Limits, breaches, notifications, snapshots         | Advanced Portfolio Scope |

### Defensible Project Positioning

BondGuard Pro is best described as:

> **A production-oriented integrated fixed-income risk analytics platform demonstrating quantitative finance, full-stack engineering, market-data pipelines, model governance, security controls, and operational risk workflows.**

The project is significantly broader than:

* a CRUD application,
* a dashboard-only project,
* a notebook-based VaR implementation,
* a single ML model,
* a basic portfolio tracker.

It should not be presented as equivalent to a commercial institutional risk platform without external model validation, licensed institutional data, production infrastructure, regulatory controls, and real operational usage.

---

# Engineering Highlights

## 1. Analytics Integrated into a Complete System

Financial models are not isolated in notebooks.

```text
Market Data
    ↓
Data Quality
    ↓
Portfolio Valuation
    ↓
Risk Calculation
    ↓
Stress Testing
    ↓
Limit Evaluation
    ↓
Breach Management
    ↓
Notifications
    ↓
Historical Snapshots
    ↓
Executive Reporting
```

This end-to-end integration is one of the project's strongest engineering characteristics.

---

## 2. Explicit Model Governance

The platform makes model behavior visible and testable.

Examples include:

* Minimum 252-observation requirement for production VaR
* Explicit `FULL_FACTOR_MODEL` state
* Explicit `RATE_ONLY_MODEL` state
* Blocked production runs when core history is insufficient
* Explicit Treasury CS01 behavior
* Documented P&L Explain residual behavior
* Deterministic pricing conventions

The objective is to expose model assumptions and degraded states rather than hide them behind successful API responses.

---

## 3. Operational Risk Workflow

BondGuard Pro connects analytical outputs to risk-management operations.

```text
Risk Metric
     ↓
Limit Evaluation
     ↓
Breach Detection
     ↓
Deduplication
     ↓
OPEN
     ↓
ACKNOWLEDGED
     ↓
RESOLVED
     ↓
Audit History
```

This moves the project beyond pure analytics into risk workflow engineering.

---

## 4. Multi-Layer Verification

The project uses multiple verification layers:

* Deterministic unit tests
* Domain service tests
* API integration tests
* Database execution tests
* RBAC authorization tests
* Data-quality tests
* Frontend component tests
* TypeScript compilation
* Backend linting
* Frontend production build validation

Current benchmark:

```text
178 automated tests passing
0 TypeScript errors
```

---

## 5. Graceful Model Degradation

A financial model should not silently return misleading confidence.

BondGuard Pro distinguishes between:

```text
FULL_FACTOR_MODEL
```

and:

```text
RATE_ONLY_MODEL
```

If required core data is insufficient, the production risk run is blocked.

This provides a clear model-state contract between the data-quality layer, risk engine, API, and frontend.

---

# API Architecture

The REST API is versioned under:

```text
/api/v1/
```

Primary API domains include:

```text
/api/v1/auth
/api/v1/portfolios
/api/v1/bonds
/api/v1/positions
/api/v1/risk
/api/v1/stress
/api/v1/scenarios
/api/v1/liquidity
/api/v1/concentration
/api/v1/risk-limits
/api/v1/breaches
/api/v1/notifications
/api/v1/reporting
/api/v1/admin
/api/v1/system
```

OpenAPI schema:

```text
http://localhost:8000/api/v1/openapi.json
```

---

# Database Architecture

The persistence layer is built with SQLAlchemy and Alembic.

Major data domains include:

```text
Identity Domain
├── Users
├── Roles
├── Permissions
└── Refresh Tokens

Portfolio Domain
├── Portfolios
├── Bonds
├── Transactions
└── Positions

Market Data Domain
├── Yield Curve Data
├── Credit Spread Data
├── Macro Data
└── ETF Market Data

Risk Domain
├── Risk Results
├── Stress Results
├── Scenario Results
└── Risk Snapshots

Control Domain
├── Risk Limits
├── Breaches
├── Breach Events
├── Notifications
└── Audit Records
```

PostgreSQL is the production database.

SQLite is used only for isolated automated tests.

---

# Installation

## Prerequisites

Install:

* Python 3.10+
* Node.js 18+
* PostgreSQL 14+
* Git
* Docker Desktop, if using containerized startup

Clone the repository:

```bash
git clone <your-repository-url>
cd bondguard-pro
```

---

# Environment Configuration

Create environment files:

```bash
cp .env.example .env
cp .env.example backend/.env
```

Configure:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/bondguard_db
FRED_API_KEY=your_fred_api_key
JWT_SECRET_KEY=replace_with_a_secure_secret
ENVIRONMENT=development
```

Never commit production secrets or local `.env` files.

---

# Database Migrations

From the backend directory:

```bash
cd backend
python -m alembic upgrade head
```

Verify the current revision:

```bash
python -m alembic current
```

Inspect migration history:

```bash
python -m alembic history
```

---

# Seed Data

Run from `backend/`:

```bash
python -m scripts.seed.seed_roles_permissions
python -m scripts.seed.seed_portfolio
python -m scripts.seed.seed_stress_scenarios
python -m scripts.seed.seed_liquidity_assumptions
python -m scripts.seed.seed_concentration_limits
python -m scripts.seed.seed_risk_limits
```

The seed scripts establish baseline roles, permissions, portfolio data, stress scenarios, liquidity assumptions, concentration limits, and risk limits for local development and demonstration workflows.

---

# Running the Application

## Backend

Create the virtual environment:

```bash
cd backend
python -m venv venv
```

Activate on Windows:

```powershell
.\venv\Scripts\activate
```

Activate on Linux or macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Backend development address:

```text
http://localhost:8000
```

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend development address:

```text
http://localhost:5173
```

---

# Docker

Start the complete stack:

```bash
docker compose up --build
```

| Service         | Port |
| --------------- | ---: |
| FastAPI Backend | 8000 |
| React Frontend  | 5173 |
| PostgreSQL      | 5432 |

Stop services:

```bash
docker compose down
```

---

# Testing and Quality Gates

## Backend

```powershell
cd backend
$env:PYTHONPATH="."
python -m pytest -v
python -m ruff check .
```

Current verified benchmark:

```text
153 / 153 backend tests passing
```

Backend verification includes:

* Clean price
* Dirty price
* Accrued interest
* Duration
* DV01 sign convention
* Convexity
* Portfolio valuation
* Historical VaR
* Parametric VaR
* Expected Shortfall
* Liquidity scoring
* Concentration analysis
* Stress testing
* Scenario Lab
* CS01
* Breach lifecycle transitions
* Breach deduplication
* RBAC constraints
* Data-quality validation
* Degraded model operation
* API integration behavior

---

## Frontend

```bash
cd frontend
npm run test -- --run
npm run build
```

Current verified benchmark:

```text
25 / 25 frontend tests passing
TypeScript errors: 0
```

Frontend verification covers:

* Portfolio summary behavior
* Risk metric presentation
* Stress-testing workflows
* Scenario Lab behavior
* Risk-limit monitoring
* Breach alerts
* RBAC route behavior
* Administrative views
* Data freshness states

---

## Verification Matrix

| Functional Domain   | Backend Verification                     | Frontend Verification  | Status   |
| ------------------- | ---------------------------------------- | ---------------------- | -------- |
| Portfolio Valuation | Clean/Dirty Price, Accrued Interest, P&L | Summary & Metric Cards | Verified |
| Rate Risk           | DV01, Duration, Convexity, KRD           | Market Risk Views      | Verified |
| Market Risk         | Historical VaR, Parametric VaR, ES       | Risk Dashboard         | Verified |
| Liquidity           | Score & Capacity Degradation             | Liquidity Profile      | Verified |
| Concentration       | Issuer & Sector HHI                      | Concentration Charts   | Verified |
| Stress Testing      | Full Revaluation & Approximation         | Stress Analysis        | Verified |
| Scenario Lab        | Custom Shocks & Attribution              | Scenario Builder       | Verified |
| Credit Sensitivity  | CS01                                     | Risk Analytics         | Verified |
| Risk Control        | Limit Evaluation & Lifecycle             | Limit Monitoring       | Verified |
| RBAC                | Reader, Analyst, Manager, Admin          | Protected Routes       | Verified |
| Data Quality        | Freshness, Outliers, Observations        | Freshness Monitor      | Verified |
| Reporting           | PDF & CSV Generation                     | Reporting Interface    | Verified |

---

# Model Governance

BondGuard Pro follows explicit model-governance principles.

## 1. No Silent Model Degradation

When credit-spread history fails validation while rate data remains usable, the system explicitly reports:

```text
RATE_ONLY_MODEL
```

The platform does not silently present rate-only results as full-factor calculations.

---

## 2. Minimum Observation Enforcement

Production VaR requires:

```text
minimum_observations = 252
```

Runs below this threshold are blocked rather than presented as production-quality results.

---

## 3. Deterministic Pricing

Pricing calculations are deterministic and testable.

The same:

* Bond terms
* Valuation date
* Yield
* Curve
* Spread assumptions

produce reproducible analytical results.

---

## 4. Explicit Sensitivity Conventions

DV01 follows the platform's documented sign convention.

CS01 is applied only to spread-sensitive instruments.

Treasuries have:

```text
CS01 = 0
```

---

## 5. Auditable Risk Control

Breach state transitions are persisted.

```text
OPEN
   ↓
ACKNOWLEDGED
   ↓
RESOLVED
```

The workflow allows operational risk events to be reviewed historically.

---

# Known Model Limitations

## Rate-Only Model Degradation

When credit-spread history fails quality gates or required external spread data is unavailable, the VaR engine may operate in:

```text
RATE_ONLY_MODEL
```

This behavior is intentional and explicitly surfaced through the API and frontend.

---

## Minimum Observations

Production VaR requires at least 252 trading-day observations.

Shorter histories are not accepted as production risk runs.

---

## Spread Duration

Treasury securities have zero spread sensitivity by construction.

CS01 is non-zero only for supported spread-sensitive corporate instruments.

---

## P&L Explain

The residual component captures effects not completely explained by the analytical decomposition.

A non-zero residual is not automatically an error condition.

---

## Carry and Roll-Down

Carry and roll-down calculations use deterministic yield-curve interpolation and shifted-maturity assumptions.

The implementation does not model stochastic interest-rate dynamics.

---

## External Data Dependencies

External market-data availability depends on upstream providers.

The platform includes data-quality controls and degraded operating modes, but these controls do not eliminate upstream data-source risk.

---

# Production Considerations

The repository demonstrates a production-oriented architecture, but deployment into a regulated institutional environment would additionally require organization-specific infrastructure and governance controls such as:

* Managed secrets infrastructure
* TLS termination
* Production identity-provider integration
* Database encryption policies
* Centralized observability
* Distributed tracing
* Backup and recovery policies
* Disaster recovery testing
* Formal model validation
* Independent price verification
* Licensed institutional market-data feeds
* Regulatory reporting controls
* Penetration testing
* Organization-specific retention policies
* Service-level objectives
* High-availability architecture

The current platform should be evaluated as an institutional-style engineering and quantitative portfolio project, not as a substitute for independently validated regulated risk infrastructure.

---

# Engineering Principles

BondGuard Pro is built around the following principles:

```text
Correctness before complexity

Explicit degradation before silent failure

Backend authorization before UI-only security

Reproducible calculations before opaque analytics

Data quality before model execution

Auditability before operational convenience

Integration testing before isolated confidence

Clear model limitations before exaggerated claims
```

---

# Screenshots and Demo

Recommended asset structure:

```text
docs/assets/
├── bondguard-demo.gif
├── executive-dashboard.png
├── portfolio-overview.png
├── market-risk-dashboard.png
├── stress-testing.png
├── scenario-lab.png
├── liquidity-risk.png
├── concentration-analysis.png
├── breach-management.png
├── data-quality-monitor.png
└── admin-console.png
```

## Suggested Demo Flow

A short product demo should show:

```text
Login
  ↓
Executive Dashboard
  ↓
Portfolio Analytics
  ↓
Market Risk
  ↓
Run Stress Scenario
  ↓
Scenario Lab
  ↓
Risk Limit Breach
  ↓
Breach Acknowledgement
  ↓
Executive Report
```

The demo should be short enough that a recruiter or technical reviewer can understand the product flow quickly.

---

# Documentation

| Topic                  | Location                                      |
| ---------------------- | --------------------------------------------- |
| System Architecture    | `docs/architecture/system_architecture.md`    |
| Data Sources           | `docs/architecture/data_sources.md`           |
| Reporting Architecture | `docs/architecture/reporting_architecture.md` |
| Portfolio Engine       | `docs/domain/portfolio_engine.md`             |
| Risk Engine            | `docs/domain/risk_engine.md`                  |
| Stress Testing         | `docs/domain/stress_testing.md`               |
| Reporting Contract     | `docs/domain/reporting_contract.md`           |
| Breach Management      | `docs/operations/breach_management.md`        |
| Risk Control           | `docs/operations/risk_control.md`             |
| Risk Snapshots         | `docs/operations/risk_snapshots.md`           |
| Development Standards  | `docs/governance/development.md`              |
| AI Agent Guidelines    | `AGENTS.md`                                   |

---

# Roadmap

Potential future extensions include:

* Multi-currency portfolio analytics
* FX risk decomposition
* Inflation-linked bond analytics
* Callable bond modeling
* Mortgage-backed security analytics
* Monte Carlo VaR
* Filtered Historical Simulation
* Expected Shortfall attribution
* Factor backtesting
* VaR exception analysis
* Basel traffic-light backtesting
* Benchmark-relative risk
* Tracking error
* Spread curve construction
* Portfolio optimization
* WebSocket-based live risk updates
* Distributed task execution
* Institutional identity-provider integration
* Cloud-native deployment
* Centralized observability

---

# Project Status

```text
Portfolio Engine             Complete
Deterministic Pricing        Complete
Market Data Pipeline         Complete
Data Quality Gate            Complete

Historical VaR               Complete
Parametric VaR               Complete
Expected Shortfall           Complete

Liquidity Analytics          Complete
Concentration Analytics      Complete
Stress Testing               Complete
Scenario Lab                 Complete
Advanced Risk Analytics      Complete

Risk Limit Framework         Complete
Breach Lifecycle             Complete
Notification Workflow        Complete

Authentication & RBAC        Complete
Historical Risk Snapshots    Complete
Executive Reporting          Complete
Frontend Analytics           Complete

Backend Test Suite           153 / 153 Passing
Frontend Test Suite           25 / 25 Passing
Total Automated Tests        178 Passing
TypeScript Errors              0
```

---

# Project Maturity

A useful way to evaluate software-project maturity is:

```text
Level 1 — Analytical Prototype

Notebook calculations
Static datasets
Isolated analytical models


Level 2 — Application

API
Database
Frontend
Basic authentication


Level 3 — Integrated Risk Platform

Data pipeline
Data quality
Portfolio valuation
Risk analytics
Stress testing
Scenario analysis
Risk controls
Breach workflows
Notifications
Historical snapshots
Reporting
RBAC
Automated verification


Level 4 — Production Institutional System

Licensed market data
Formal independent model validation
Enterprise IAM
High availability
Disaster recovery
Centralized observability
Operational SLOs
Regulatory controls
Independent price verification
Real production usage
```

BondGuard Pro is designed toward:

> **Level 3 — Integrated Risk Platform**

This is the strongest defensible positioning based on the implemented capabilities described in the repository.

The project is substantially more complete than a notebook, dashboard, CRUD portfolio application, or isolated analytical model while remaining transparent about the additional controls required for real institutional deployment.

---

# What This Project Demonstrates

## Quantitative Finance

* Fixed-income pricing
* Duration and convexity
* DV01
* Key Rate Duration
* Bucketed DV01
* CS01
* Historical VaR
* Parametric VaR
* Expected Shortfall
* Liquidity risk
* Concentration analysis
* Stress testing
* Scenario analysis
* Carry and roll-down
* P&L Explain

## Backend Engineering

* FastAPI architecture
* Domain-oriented service separation
* REST API design
* SQLAlchemy persistence
* Alembic migrations
* JWT authentication
* Refresh token lifecycle
* RBAC
* Reporting services
* Data workflows

## Data Engineering

* External API ingestion
* Pipeline orchestration
* Data normalization
* Freshness validation
* Observation-count enforcement
* Outlier detection
* Explicit model degradation

## Frontend Engineering

* React
* TypeScript
* TanStack Query
* Plotly analytics
* Protected routes
* Permission-aware interfaces
* Analytical dashboard design

## Software Quality

* Automated backend testing
* Frontend component testing
* Integration testing
* Database isolation
* Linting
* Type checking
* Containerized execution

# Why BondGuard Pro?

Most portfolio projects stop at displaying prices or calculating a single risk metric.

BondGuard Pro is structured as a complete analytical and operational risk platform:

```text
Data
  → Validation
    → Valuation
      → Risk
        → Stress
          → Scenarios
            → Limits
              → Breaches
                → Notifications
                  → Snapshots
                    → Reporting
```

The goal is not only to calculate financial metrics.

The project demonstrates how quantitative finance, backend engineering, data pipelines, frontend analytics, authentication, authorization, model governance, testing, reporting, and operational risk workflows can be integrated into one coherent platform.

---

## BondGuard Pro

**Integrated Fixed-Income Portfolio Risk Analytics Platform**

Built with Python, FastAPI, PostgreSQL, React, TypeScript, and quantitative risk analytics.
