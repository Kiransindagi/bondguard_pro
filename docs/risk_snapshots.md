# Risk Snapshots

## Purpose
`PortfolioRiskSnapshot` captures the end-of-day state of a portfolio's risk profile. It enables historical trend analysis for Modified Duration, DV01, Historical VaR, Market Value, Liquidity Score, and active risk breaches.

## Rules & Properties
* **Uniqueness**: Only one snapshot per portfolio per day (`snapshot_date`).
* **Idempotent Updates**: Generating a snapshot on an existing day executes an *upsert*, ensuring intraday reruns overwrite the daily aggregate without generating duplicate snapshots.
* **Preservation**: Unavailable data points persist gracefully as `null` in the PostgreSQL database.

## Model
Stored in the `portfolio_risk_snapshots` table, containing financial columns as `Numeric(18, 6)` or `Float`. Includes model governance properties like `market_risk_model_status` and `liquidity_model_type` to preserve historical model degradation events.
