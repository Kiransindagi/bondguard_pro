from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from .exceptions import InvalidInputError
from .types import CashFlow


def get_frequency_months(frequency: str) -> int:
    if frequency == "annual":
        return 12
    elif frequency == "semiannual":
        return 6
    elif frequency == "quarterly":
        return 3
    else:
        raise InvalidInputError(f"Unknown frequency: {frequency}")

def get_periods_per_year(frequency: str) -> int:
    if frequency == "annual":
        return 1
    elif frequency == "semiannual":
        return 2
    elif frequency == "quarterly":
        return 4
    else:
        raise InvalidInputError(f"Unknown frequency: {frequency}")

def days_between(d1: date, d2: date, convention: str) -> int:
    if convention == "ACT/ACT" or convention == "ACT/360":
        return (d2 - d1).days
    elif convention == "30/360":
        d1_d = d1.day
        d2_d = d2.day
        if d1_d == 31:
            d1_d = 30
        if d2_d == 31 and d1_d == 30:
            d2_d = 30
        return 360 * (d2.year - d1.year) + 30 * (d2.month - d1.month) + (d2_d - d1_d)
    else:
        raise InvalidInputError(f"Unknown day count convention: {convention}")

def days_in_year(d: date, convention: str) -> Decimal:
    if convention == "ACT/360" or convention == "30/360":
        return Decimal(360)
    elif convention == "ACT/ACT":
        import calendar
        return Decimal(366) if calendar.isleap(d.year) else Decimal(365)
    else:
        raise InvalidInputError(f"Unknown day count convention: {convention}")

def generate_coupon_schedule(issue_date: date, maturity_date: date, frequency: str) -> list[date]:
    months_step = get_frequency_months(frequency)
    schedule = []
    current = maturity_date
    while current > issue_date:
        schedule.insert(0, current)
        current = current - relativedelta(months=months_step)
    return schedule

def calculate_accrued_interest(settlement_date: date, issue_date: date, maturity_date: date,
                               face_value: Decimal, coupon_rate: Decimal, frequency: str, convention: str) -> Decimal:
    if settlement_date <= issue_date:
        return Decimal(0)
    if settlement_date >= maturity_date:
        return Decimal(0)

    schedule = generate_coupon_schedule(issue_date, maturity_date, frequency)
    prev_coupon_date = issue_date
    for dt in schedule:
        if dt > settlement_date:
            break
        prev_coupon_date = dt

    days = days_between(prev_coupon_date, settlement_date, convention)
    days_year = days_in_year(settlement_date, convention)
    
    return face_value * coupon_rate * Decimal(days) / days_year

def generate_remaining_cashflows(settlement_date: date, issue_date: date, maturity_date: date, 
                                 face_value: Decimal, coupon_rate: Decimal, frequency: str, convention: str) -> list[CashFlow]:
    if settlement_date >= maturity_date:
        return []

    schedule = generate_coupon_schedule(issue_date, maturity_date, frequency)
    periods_per_year = Decimal(get_periods_per_year(frequency))
    coupon_pmt = face_value * coupon_rate / periods_per_year

    cashflows = []
    for dt in schedule:
        if dt <= settlement_date:
            continue
        
        days = days_between(settlement_date, dt, convention)
        days_year = days_in_year(settlement_date, convention)
        t_years = Decimal(days) / days_year

        is_maturity = (dt == maturity_date)
        principal = face_value if is_maturity else Decimal(0)
        total_cf = coupon_pmt + principal

        cashflows.append(CashFlow(
            payment_date=dt,
            coupon_amount=coupon_pmt,
            principal_amount=principal,
            total_cash_flow=total_cf,
            time_in_years=t_years
        ))
    return cashflows
