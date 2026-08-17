from datetime import date
from decimal import Decimal

from app.risk_engine.cashflows import generate_remaining_cashflows
from app.risk_engine.convexity import calculate_convexity
from app.risk_engine.curve import YieldCurve
from app.risk_engine.duration import calculate_macaulay_duration
from app.risk_engine.dv01 import calculate_dv01
from app.risk_engine.valuation import dirty_price_from_ytm
from app.risk_engine.yield_solver import calculate_ytm


def test_cashflows_annual_schedule():
    issue = date(2020, 1, 1)
    maturity = date(2025, 1, 1)
    settlement = date(2022, 6, 1)
    
    # Generate remaining cashflows
    cfs = generate_remaining_cashflows(settlement, issue, maturity, Decimal(100), Decimal('0.05'), 'annual', '30/360')
    assert len(cfs) == 3
    assert cfs[0].payment_date == date(2023, 1, 1)
    assert cfs[1].payment_date == date(2024, 1, 1)
    assert cfs[-1].payment_date == date(2025, 1, 1)
    assert cfs[-1].principal_amount == Decimal(100)
    assert cfs[-1].total_cash_flow == Decimal(105)

def test_matured_bond_cashflows():
    issue = date(2020, 1, 1)
    maturity = date(2022, 1, 1)
    settlement = date(2022, 6, 1)
    cfs = generate_remaining_cashflows(settlement, issue, maturity, Decimal(100), Decimal('0.05'), 'annual', '30/360')
    assert len(cfs) == 0

def test_ytm_par_bond():
    issue = date(2020, 1, 1)
    maturity = date(2025, 1, 1)
    settlement = date(2020, 1, 1) # issue date
    cfs = generate_remaining_cashflows(settlement, issue, maturity, Decimal(100), Decimal('0.05'), 'annual', '30/360')
    
    dirty_price = Decimal('100.0')
    ytm = calculate_ytm(cfs, dirty_price, 'annual')
    # Par bond with 5% coupon should yield exactly 5% (0.05)
    assert round(ytm, 4) == Decimal('0.0500')

def test_ytm_premium_bond():
    issue = date(2020, 1, 1)
    maturity = date(2025, 1, 1)
    settlement = date(2020, 1, 1)
    cfs = generate_remaining_cashflows(settlement, issue, maturity, Decimal(100), Decimal('0.05'), 'annual', '30/360')
    
    dirty_price = Decimal('105.0')
    ytm = calculate_ytm(cfs, dirty_price, 'annual')
    assert ytm < Decimal('0.05')

def test_ytm_discount_bond():
    issue = date(2020, 1, 1)
    maturity = date(2025, 1, 1)
    settlement = date(2020, 1, 1)
    cfs = generate_remaining_cashflows(settlement, issue, maturity, Decimal(100), Decimal('0.05'), 'annual', '30/360')
    
    dirty_price = Decimal('95.0')
    ytm = calculate_ytm(cfs, dirty_price, 'annual')
    assert ytm > Decimal('0.05')

def test_yield_price_yield_roundtrip():
    issue = date(2020, 1, 1)
    maturity = date(2025, 1, 1)
    settlement = date(2021, 5, 1)
    cfs = generate_remaining_cashflows(settlement, issue, maturity, Decimal(100), Decimal('0.05'), 'semiannual', '30/360')
    
    original_ytm = Decimal('0.0425')
    dirty = dirty_price_from_ytm(cfs, original_ytm, 'semiannual')
    recovered_ytm = calculate_ytm(cfs, dirty, 'semiannual')
    assert round(original_ytm, 8) == round(recovered_ytm, 8)

def test_macaulay_duration_zero_coupon():
    issue = date(2020, 1, 1)
    maturity = date(2025, 1, 1)
    settlement = date(2020, 1, 1)
    # Zero coupon bond
    cfs = generate_remaining_cashflows(settlement, issue, maturity, Decimal(100), Decimal('0.0'), 'annual', '30/360')
    ytm = Decimal('0.05')
    dirty = dirty_price_from_ytm(cfs, ytm, 'annual')
    mac_dur = calculate_macaulay_duration(cfs, ytm, 'annual', dirty)
    # Macaulay duration of zero coupon is exact time to maturity
    assert round(mac_dur, 2) == Decimal('5.00')

def test_convexity_positive():
    issue = date(2020, 1, 1)
    maturity = date(2025, 1, 1)
    settlement = date(2020, 1, 1)
    cfs = generate_remaining_cashflows(settlement, issue, maturity, Decimal(100), Decimal('0.05'), 'annual', '30/360')
    ytm = Decimal('0.05')
    dirty = dirty_price_from_ytm(cfs, ytm, 'annual')
    conv = calculate_convexity(cfs, ytm, 'annual', dirty)
    assert conv > Decimal(0)

def test_dv01_finite_difference():
    issue = date(2020, 1, 1)
    maturity = date(2025, 1, 1)
    settlement = date(2020, 1, 1)
    cfs = generate_remaining_cashflows(settlement, issue, maturity, Decimal(100), Decimal('0.05'), 'annual', '30/360')
    ytm = Decimal('0.05')
    dirty = dirty_price_from_ytm(cfs, ytm, 'annual')
    
    dv01 = calculate_dv01(cfs, ytm, 'annual', dirty, face_value=Decimal(100), quantity=Decimal(1))
    assert dv01 > Decimal(0)

def test_curve_interpolation():
    points = {
        2.0: Decimal('0.02'),
        5.0: Decimal('0.03'),
        10.0: Decimal('0.04')
    }
    curve = YieldCurve(points)
    assert curve.get_yield(2.0) == Decimal('0.02')
    assert round(curve.get_yield(3.5), 4) == Decimal('0.025')
    assert curve.get_yield(1.0) == Decimal('0.02') # Lower bound extrapolation
    assert curve.get_yield(15.0) == Decimal('0.04') # Upper bound extrapolation
