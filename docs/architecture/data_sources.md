# Data Sources

BondGuard Pro relies on external data sources for portfolio pricing, macro conditions, and risk intelligence.

## 1. FRED API (Federal Reserve Economic Data)
Used for macro and rates context.

**Treasury Yield Curve**
*   2Y: DGS2
*   5Y: DGS5
*   10Y: DGS10
*   30Y: DGS30

*Stored in `yield_curve_points` in percentages (e.g., 4.25 means 4.25%).*

**Macro & Credit Spreads**
*   Effective Fed Funds Rate: DFF (Stored in `macro_observations`)
*   IG Corporate Spread: BAMLC0A0CM (Stored in `credit_spreads` in basis points. Example: 150 bps)
*   HY Corporate Spread: BAMLH0A0HYM2 (Stored in `credit_spreads` in basis points. Example: 325 bps)

## 2. ETF Market Data Proxies
We use `yfinance` as a development/demo data adapter. This runs behind a `MarketDataProvider` abstraction interface and stores data to `market_prices`.

**Initial ETFs**
*   SHY: Short Treasury
*   IEF: Intermediate Treasury
*   TLT: Long Treasury
*   LQD: Investment Grade Corporate
*   HYG: High Yield Corporate
*   EMB: Emerging Market Debt

## Ingestion
Data is fetched via the CLI:
`python ingest.py --dataset all`

All ingestion runs are tracked in `data_ingestion_runs`. Runs will be marked as `RUNNING`, `SUCCESS`, `PARTIAL`, or `FAILED`.
