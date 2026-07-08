from datetime import date
from decimal import Decimal
from typing import List, Tuple
from dateutil.relativedelta import relativedelta

def _get_frequency_months(frequency: str) -> int:
    if frequency == "annual": return 12
    elif frequency == "semiannual": return 6
    elif frequency == "quarterly": return 3
    else: raise ValueError(f"Unknown frequency: {frequency}")

def generate_coupon_schedule(issue_date: date, maturity_date: date, frequency: str) -> List[date]:
    months_step = _get_frequency_months(frequency)
    schedule = []
    current = maturity_date
    while current > issue_date:
        schedule.insert(0, current)
        current = current - relativedelta(months=months_step)
    return schedule

def calculate_cash_flows(face_value: Decimal, coupon_rate: Decimal, frequency: str, schedule: List[date]) -> List[Tuple[date, Decimal]]:
    if not schedule:
        return []
    months_step = _get_frequency_months(frequency)
    periods_per_year = Decimal(12) / Decimal(months_step)
    coupon_pmt = face_value * coupon_rate / periods_per_year
    cash_flows = []
    for dt in schedule[:-1]:
        cash_flows.append((dt, coupon_pmt))
    
    # Last payment includes principal
    cash_flows.append((schedule[-1], coupon_pmt + face_value))
    return cash_flows

def _days_between(d1: date, d2: date, convention: str) -> int:
    if convention == "ACT/ACT" or convention == "ACT/360":
        return (d2 - d1).days
    elif convention == "30/360":
        d1_d = d1.day
        d2_d = d2.day
        if d1_d == 31: d1_d = 30
        if d2_d == 31 and d1_d == 30: d2_d = 30
        return 360 * (d2.year - d1.year) + 30 * (d2.month - d1.month) + (d2_d - d1_d)
    else:
        raise ValueError(f"Unknown day count convention: {convention}")

def _days_in_year(d: date, convention: str) -> Decimal:
    if convention == "ACT/360" or convention == "30/360":
        return Decimal(360)
    elif convention == "ACT/ACT":
        # Simplified: use 365 or 366
        import calendar
        return Decimal(366) if calendar.isleap(d.year) else Decimal(365)
    else:
        raise ValueError(f"Unknown day count convention: {convention}")

def calculate_accrued_interest(settlement_date: date, issue_date: date, schedule: List[date], 
                               face_value: Decimal, coupon_rate: Decimal, convention: str) -> Decimal:
    if settlement_date <= issue_date: return Decimal('0')
    if settlement_date >= schedule[-1]: return Decimal('0')

    prev_coupon_date = issue_date
    for dt in schedule:
        if dt > settlement_date:
            break
        prev_coupon_date = dt

    days = _days_between(prev_coupon_date, settlement_date, convention)
    days_year = _days_in_year(settlement_date, convention)
    
    return face_value * coupon_rate * Decimal(days) / days_year

def calculate_dirty_price(cash_flows: List[Tuple[date, Decimal]], settlement_date: date, ytm: Decimal, convention: str) -> Decimal:
    price = Decimal('0')
    for dt, cf in cash_flows:
        if dt <= settlement_date: continue
        days = _days_between(settlement_date, dt, convention)
        days_year = _days_in_year(settlement_date, convention)
        years = Decimal(days) / days_year
        # Continuous compounding approximation for simplicity, or discrete: cf / (1+ytm)^years
        # Using discrete:
        price += cf / ((Decimal('1') + ytm) ** years)
    return price

def clean_to_dirty_price(clean_price: Decimal, accrued_interest: Decimal) -> Decimal:
    return clean_price + accrued_interest

def dirty_to_clean_price(dirty_price: Decimal, accrued_interest: Decimal) -> Decimal:
    return dirty_price - accrued_interest
