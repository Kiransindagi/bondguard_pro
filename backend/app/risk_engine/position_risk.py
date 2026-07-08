from decimal import Decimal
from .types import BondRiskInput, BondRiskResult
from .cashflows import generate_remaining_cashflows, calculate_accrued_interest
from .yield_solver import calculate_ytm
from .valuation import dirty_price_from_ytm
from .duration import calculate_macaulay_duration, calculate_modified_duration
from .convexity import calculate_convexity
from .dv01 import calculate_dv01

def calculate_position_risk(input_data: BondRiskInput) -> BondRiskResult:
    """
    Calculate full risk metrics for a single bond position.
    """
    ai = calculate_accrued_interest(
        input_data.valuation_date, input_data.issue_date, input_data.maturity_date,
        input_data.face_value, input_data.coupon_rate, input_data.coupon_frequency,
        input_data.day_count_convention
    )

    cashflows = generate_remaining_cashflows(
        input_data.valuation_date, input_data.issue_date, input_data.maturity_date,
        input_data.face_value, input_data.coupon_rate, input_data.coupon_frequency,
        input_data.day_count_convention
    )

    # Determine dirty price and YTM based on input
    if input_data.valuation_date >= input_data.maturity_date:
        clean_price = Decimal('0')
        dirty_price = Decimal('0')
        ytm = Decimal('0')
    else:
        if input_data.clean_price is not None and input_data.ytm is not None:
            # If both are provided, we should probably prefer price or yield, but we'll use price for solving yield to be safe
            dirty_price = input_data.clean_price + ai
            ytm = calculate_ytm(cashflows, dirty_price, input_data.coupon_frequency)
            clean_price = input_data.clean_price
        elif input_data.clean_price is not None:
            dirty_price = input_data.clean_price + ai
            ytm = calculate_ytm(cashflows, dirty_price, input_data.coupon_frequency)
            clean_price = input_data.clean_price
        elif input_data.ytm is not None:
            ytm = input_data.ytm
            dirty_price = dirty_price_from_ytm(cashflows, ytm, input_data.coupon_frequency)
            clean_price = dirty_price - ai
        else:
            # Neither provided, cannot calculate
            raise ValueError("Either clean_price or ytm must be provided")

    market_value = input_data.quantity * input_data.face_value * clean_price / Decimal('100.0')

    mac_dur = calculate_macaulay_duration(cashflows, ytm, input_data.coupon_frequency, dirty_price)
    mod_dur = calculate_modified_duration(mac_dur, ytm, input_data.coupon_frequency)
    conv = calculate_convexity(cashflows, ytm, input_data.coupon_frequency, dirty_price)
    dv01 = calculate_dv01(cashflows, ytm, input_data.coupon_frequency, dirty_price, input_data.face_value, input_data.quantity)

    return BondRiskResult(
        bond_id=input_data.bond_id,
        valuation_date=input_data.valuation_date,
        clean_price=clean_price,
        dirty_price=dirty_price,
        accrued_interest=ai,
        ytm_decimal=ytm,
        macaulay_duration_years=mac_dur,
        modified_duration_years=mod_dur,
        convexity=conv,
        dv01_currency=dv01,
        market_value=market_value
    )
