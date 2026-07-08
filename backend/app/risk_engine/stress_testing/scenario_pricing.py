from datetime import date
from decimal import Decimal
from app.db.models import Bond, Position
from app.risk_engine.types import BondRiskResult
from app.risk_engine.curve import YieldCurve
from app.risk_engine.valuation import clean_price_from_ytm
from app.risk_engine.cashflows import generate_remaining_cashflows, calculate_accrued_interest
from app.risk_engine.yield_solver import calculate_ytm
from .types import CalculationMethod
from .curve_shocks import interpolate_rate_shock
from .spread_shocks import resolve_spread_shock

def get_base_yield(bond: Bond, valuation_date: date, curve: YieldCurve, issue_price: Decimal) -> Decimal:
    """
    Get the base yield for a bond.
    """
    # Create a generic BondRiskInput to calculate YTM if needed or use curve.
    cf = generate_remaining_cashflows(
        valuation_date,
        bond.issue_date,
        bond.maturity_date,
        Decimal(str(bond.face_value)),
        Decimal(str(bond.coupon_rate)),
        bond.coupon_frequency,
        bond.day_count_convention
    )
    if not cf:
        return Decimal('0')
    accrued = calculate_accrued_interest(
        valuation_date, 
        bond.issue_date, 
        bond.maturity_date, 
        Decimal(str(bond.face_value)), 
        Decimal(str(bond.coupon_rate)), 
        bond.coupon_frequency, 
        bond.day_count_convention
    )
    
    # Try solving YTM from issue_price if available, otherwise use curve
    try:
        if issue_price:
            dirty = issue_price + accrued
            return calculate_ytm(cf, dirty, bond.coupon_frequency)
    except Exception:
        pass
        
    maturity_years = (bond.maturity_date - valuation_date).days / 365.25
    rate = curve.get_rate(maturity_years)
    
    # Simple proxy: if corporate, add a fixed spread just to get a base yield, or just use rate.
    # For scenario pricing, base yield is rate + some spread.
    base_spread = Decimal('0')
    if getattr(bond, "bond_type", None) == "Corporate":
        base_spread = Decimal('0.01') # 100 bps base spread proxy
        
    return rate + base_spread

def calculate_scenario_pricing(
    bond: Bond,
    position: Position,
    valuation_date: date,
    base_risk: BondRiskResult,
    rate_2y_bps: float,
    rate_5y_bps: float,
    rate_10y_bps: float,
    rate_30y_bps: float,
    ig_spread_bps: float,
    hy_spread_bps: float,
    method: CalculationMethod
) -> tuple[Decimal, Decimal]:
    """
    Calculate stressed clean price and market value.
    Returns (stressed_clean_price, stressed_market_value)
    """
    maturity_years = max(0.0, (bond.maturity_date - valuation_date).days / 365.25)
    
    # Convert bps to decimal percent
    rate_shock = interpolate_rate_shock(maturity_years, rate_2y_bps, rate_5y_bps, rate_10y_bps, rate_30y_bps) / 10000.0
    spread_shock = resolve_spread_shock(bond, ig_spread_bps, hy_spread_bps) / 10000.0
    
    if method == CalculationMethod.APPROXIMATION:
        dv01 = Decimal(str(base_risk.dv01_currency))
        # Approximation: PnL = -DV01 * (rate_shock_bps + spread_shock_bps) 
        # DV01 is per 1bp.
        total_shock_bps = Decimal(str((rate_shock + spread_shock) * 10000.0))
        pnl = -dv01 * total_shock_bps
        
        # Add convexity adjustment (Optional, but user said "plus convexity adjustment" roughly)
        # 1/2 * Convexity * MV * (shock_yield)^2 
        # shock_yield is decimal (e.g. 0.01 for 100bps)
        total_shock_dec = Decimal(str(rate_shock + spread_shock))
        convexity = Decimal(str(base_risk.convexity))
        base_mv = Decimal(str(base_risk.market_value))
        
        convexity_adj = Decimal('0.5') * convexity * base_mv * (total_shock_dec ** 2)
        pnl += convexity_adj
        
        stressed_mv = base_mv + pnl
        # rough clean price estimate
        stressed_price = (stressed_mv / (position.quantity * bond.face_value)) * Decimal('100')
        return stressed_price, stressed_mv
        
    elif method == CalculationMethod.FULL_REVALUATION:
        # Full Revaluation
        cf = generate_remaining_cashflows(
            valuation_date,
            bond.issue_date,
            bond.maturity_date,
            Decimal(str(bond.face_value)),
            Decimal(str(bond.coupon_rate)),
            bond.coupon_frequency,
            bond.day_count_convention
        )
        if not cf:
            # Matured bond
            return Decimal('100'), Decimal('0')
            
        accrued = calculate_accrued_interest(
            valuation_date, 
            bond.issue_date, 
            bond.maturity_date, 
            Decimal(str(bond.face_value)), 
            Decimal(str(bond.coupon_rate)), 
            bond.coupon_frequency, 
            bond.day_count_convention
        )
        
        base_yield = Decimal(str(base_risk.ytm_decimal))
        stressed_yield = base_yield + Decimal(str(rate_shock)) + Decimal(str(spread_shock))
        
        if rate_shock == 0 and spread_shock == 0:
            return base_risk.clean_price, base_risk.market_value
        
        # Ensure yield domain validity (cannot be <= -100%)
        if stressed_yield <= Decimal('-0.99'):
            stressed_yield = Decimal('-0.99')
            
        stressed_clean = clean_price_from_ytm(cf, stressed_yield, bond.coupon_frequency, accrued)
        stressed_mv = position.quantity * bond.face_value * (stressed_clean / Decimal('100'))
        
        return stressed_clean, stressed_mv
        
    raise ValueError(f"Unknown calculation method: {method}")
