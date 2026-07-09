# Reporting Architecture

## Overview
BondGuard Pro integrates analytical outputs from multiple independent engines into deterministic, persistent snapshots and reporting contracts. The reporting layer acts as an authoritative aggregator rather than recalculating risk metrics itself.

## Authoritative Service Composition
The `ReportingService` composes data from:
* **Portfolio Risk Summary** (Sprint 2): Valuation, PnL, duration, DV01.
* **Market Risk Engine** (Sprint 4): Historical VaR, Parametric VaR, Expected Shortfall.
* **Stress Testing Engine** (Sprint 5): Worst-case deterministic scenario execution.
* **Liquidity & Concentration** (Sprint 6): Characteristic-based proxy estimation.
* **Risk Control Evaluator** (Sprint 7): Limit adherence and breach summaries.

## Data Governance & Integrity
The system is bound by strict deterministic rules:
* Missing metrics are returned as `null` and exported as `N/A`. They are **never** coerced to `0`.
* Degraded models (e.g., `RATE_ONLY_MODEL` when spread history is insufficient) propagate their status up to the executive dashboard.
* No Language Models (LLMs) are used to dynamically narrate risk statuses; all commentary is deterministic and bounds-checked.
* The system uses `Decimal` and `Numeric` data types for exact financial computations.
