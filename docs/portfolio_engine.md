# Portfolio Engine Documentation

The Portfolio Engine forms the core of Sprint 2, handling the institutional storage and management of portfolios, bonds, transactions, and positions.

## Database Models

The schema revolves around four main entities:
*   **Portfolio**: The top-level container mapping to a specific currency and benchmark.
*   **Bond**: A unique fixed-income instrument identified by an ISIN.
*   **Transaction**: An atomic record of a `BUY` or `SELL` trade for a specific bond within a portfolio. Includes trade date, settlement date, quantity, and clean price.
*   **Position**: The rolled-up accounting view for a portfolio's ownership of a bond. Maintained via transactions.

## Position Accounting Logic

Positions are strictly transaction-driven. The `PositionService` coordinates the logic:

1.  **BUY**:
    *   Increases the total quantity held.
    *   Calculates the new **Weighted Average Cost (WAC)**:
        `New Cost = [(Current Qty * Current Cost) + (New Qty * New Clean Price)] / (Current Qty + New Qty)`
    *   Updates the `current_clean_price` and dynamically computes `market_value` and `unrealized_pnl`.

2.  **SELL**:
    *   Decreases the quantity held.
    *   Will throw an HTTP 400 error if the requested sell quantity exceeds the held quantity (overselling rejection).
    *   The `average_cost` remains unchanged during a sell. Only `current_clean_price`, `market_value`, and `unrealized_pnl` update.

## Quantity and Market Value Semantics

By convention across the BondGuard Pro platform:

*   **Quantity**: Represents the number of face-value bond units.
*   **Face Value**: The principal amount of a single unit of the bond (often 100 or 1,000).
*   **Clean Price**: Quoted as a percentage of face value.

**Market Value Formula**:
`Market Value = Quantity × Face Value × Clean Price / 100`

**Unrealized P&L Formula**:
`Unrealized P&L = Market Value - (Quantity × Face Value × Average Cost / 100)`

**Total Consideration (Transaction)**:
`Total Consideration = Quantity × Face Value × Clean Price / 100` (plus any accrued interest depending on the transaction terms).

## Pricing Concepts

*   **Clean Price**: The quoted price of the bond excluding accrued interest.
*   **Accrued Interest (AI)**: Interest earned since the last coupon payment date but not yet paid out. Calculated based on day-count conventions (ACT/ACT, ACT/360, 30/360).
*   **Dirty Price**: The actual cash consideration for the bond. `Dirty Price = Clean Price + Accrued Interest`.
