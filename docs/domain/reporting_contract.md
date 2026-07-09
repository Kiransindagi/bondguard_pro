# Reporting Contract (Sprint 7 Phase C)

## Overview
The \/api/v1/risk-control/portfolios/{id}/report\ endpoint generates an institutional-grade risk report assembling outputs from previous risk sprints.

## Schema Structure
1. **portfolio**: basic identity
2. **report_metadata**: valuation date, status
3. **portfolio_risk**: deterministic price/duration metrics
4. **market_risk**: VaR/ES and factor model status
5. **stress_risk**: predefined worst-stress performance
6. **liquidity_risk**: characteristic-based proxy estimates
7. **concentration**: issuer/sector exposure highlights
8. **limit_summary**: counts of evaluate/pass/warn/breach
9. **limit_results**: full detail of all evaluated limits, observed metrics, and utilization percent
10. **breach_summary**: counts by status
11. **active_breaches**: detailed OPEN and ACKNOWLEDGED limits
12. **model_governance**: transparent declaration of active, degraded, and proxy models, along with explicitly stated limitations.

## Degraded Models
Missing values are preserved as nulls, never converted to 0. If a metric cannot be calculated (e.g. missing credit spread data), its model status is reported as \ERROR\ or \RATE_ONLY_MODEL\, and the exact limitation is surfaced in the \model_governance\ section.
