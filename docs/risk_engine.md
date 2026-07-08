# Fixed-Income Risk Engine

The BondGuard Pro Risk Engine (Sprint 3) performs deterministic, independent fixed-income valuation and interest-rate risk metrics.

## Pricing Conventions

*   **Yield Units**: Yields are processed internally as standard decimals (e.g., `0.05` for 5%). All APIs take and return decimal yields.
*   **Price Conventions**: Prices are expressed per 100 face value.
*   **Compounding**: Standard periodic compounding based on coupon frequency (e.g., semi-annual compounding for semi-annual bonds).
*   **Quantity Scaling**: The `quantity` represents the number of face-value units. Thus, for position value, it scales as `Quantity × Face Value × Price / 100`.

## Matured Bonds

If a bond has reached its maturity date relative to the valuation date:
*   Its remaining cash flows are considered empty.
*   Accrued interest, duration, convexity, and DV01 all zero out.
*   Clean and dirty prices fall to zero for ongoing risk.

## Numerical Solver

The Yield-to-Maturity (YTM) solver relies on a pure Python implementation of the Bisection Method. It achieves convergence within 1e-8 tolerance by strictly converting Decimal representations to fast native floats within the tight iterative loop, then returns a rigorous Decimal.

## Risk Metrics

*   **Macaulay Duration**: Measured in years, representing the time-weighted average of discounted cash flows.
*   **Modified Duration**: The analytical price sensitivity to yield changes. `ModDur = MacDur / (1 + y/m)`
*   **Convexity**: Analytical bond convexity based on periodic compounding, adjusted by frequency squared.
*   **DV01 (PV01)**: The approximate monetary price change for a 1 basis-point parallel yield shift, determined via finite-difference `(Price(y - 1bp) - Price(y + 1bp)) / 2`. DV01 is reported as a positive loss magnitude for a +1bp yield increase.

## Yield Curve Interpolation

The active yield curve leverages `DGS2, DGS5, DGS10, DGS30` from the FRED data pipeline.
*   Intermediate tenor yields are extracted using **linear interpolation**.
*   Outside tenor boundaries (e.g., <2Y or >30Y), flat extrapolation is explicitly enforced (i.e., taking the boundary yield).

## Limitations (Sprint 3)

*   **No Irregular Stub Handling**: Bonds with explicitly irregular first/last coupon periods are approximated to standard lengths.
*   **Historical VaR/Monte Carlo**: Deferred to future sprints. No parametric stress testing is active in the current baseline.
*   **QuantLib Validation**: The pure internal Python engine serves as the authoritative source without dragging in the C++ bindings overhead of QuantLib under Python 3.13 environments.
