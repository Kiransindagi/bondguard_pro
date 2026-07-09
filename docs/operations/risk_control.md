# Risk Control Architecture

## Overview
BondGuard Pro evaluates portfolios against institutional risk limits. The risk engine connects metric adapters to analytical engines (Sprints 3-6) and maps them to defined RiskLimits.

## Metric Registry & Adapters
The `MetricRegistry` delegates calculation to metric-specific adapters.
* **Deterministic Risk**: Modified Duration (years), DV01 (USD), Market Value (USD)
* **Market Risk**: Historical VaR, Expected Shortfall (USD)
* **Stress Testing**: Worst Stress Loss (USD)
* **Liquidity Risk**: Liquidity Score (score), Cost (bps), Max Days (days)
* **Concentration**: Issuer/Sector Max (ratio)

If a model cannot calculate a metric (e.g. missing historical data for VaR), it returns a model status of `ERROR` with `limitations` describing the domain reason.

## Unit Contracts
Risk limit thresholds and evaluated metrics strictly use compatible units:
* Currency limits (e.g., VaR) use **USD**.
* Ratio limits (e.g., concentrations) use **decimal fractions** (not %).
* Spread/Liquidity costs use **bps**.
* Duration uses **years**.

## Limit Precedence
* Only `is_active = True` limits are evaluated.
* Limits are only evaluated if their effective dates (`effective_from`, `effective_to`) cover the valuation date.
* Portfolio-specific overrides (`PORTFOLIO` scope) supersede `GLOBAL` scope limits for the same metric type.

## Evaluation Lifecycle
Evaluation atomicity is guaranteed via a database transaction.
* If successful, an evaluation run creates `RiskLimitResult` records for each limit.
* If an unexpected adapter failure occurs, it is caught, the transaction rolls back, and a `FAILED` run is persisted to avoid orphaned/partial evaluation states.
* Controlled domain errors result in `NOT_EVALUATED` limit results rather than a total run failure.
