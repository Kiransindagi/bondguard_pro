# Executive Risk Report

## Objective
The Executive Risk Report standardizes risk reporting across portfolios for institutional stakeholders. It serves as a single source of truth for current limit adherence and portfolio risk parameters.

## Export Mediums
* **JSON API**: Contract consumed by the React `Reporting` dashboard.
* **CSV Export**: A flat, tabular export of the portfolio's historical risk snapshots.
* **PDF Export**: A deterministic, server-side generated PDF via `reportlab`.

## Structure
1. **Metadata**: Portfolio details, snapshot timestamp.
2. **Portfolio Risk**: Market value, Duration, DV01.
3. **Market Risk**: Historical VaR and model status.
4. **Stress Testing**: Worst scenario identification.
5. **Liquidity & Concentration**: Largest weights and proxy scores.
6. **Active Breaches**: Unacknowledged limit violations.
7. **Model Governance**: Transparent warnings regarding proxy data or degraded models.

## Disclaimers
All exported PDFs include:
*FOR DEMONSTRATION AND EDUCATIONAL PURPOSES. NOT INVESTMENT ADVICE. DEMONSTRATION POLICY LIMITS ARE NOT REGULATORY REQUIREMENTS.*
