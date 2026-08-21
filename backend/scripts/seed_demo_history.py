"""Populate the local demo database with deterministic market-risk history.

This script is intentionally idempotent.  It adds 270 business-day observations
for the rate and credit-spread factors used by the VaR model; it does not touch
users, portfolios, positions, or live service processes.
"""

from datetime import date, timedelta
from math import sin

from app.db.database import SessionLocal
from app.db.models import CreditSpread, YieldCurvePoint


RATE_FACTORS = {
    2.0: ("DGS2", 3.72),
    5.0: ("DGS5", 3.84),
    10.0: ("DGS10", 4.11),
    30.0: ("DGS30", 4.36),
}
SPREAD_FACTORS = {
    "IG": ("BAMLC0A0CM", 104.0),
    "HY": ("BAMLH0A0HYM2", 358.0),
}


def business_days(count: int) -> list[date]:
    days: list[date] = []
    cursor = date.today()
    while len(days) < count:
        if cursor.weekday() < 5:
            days.append(cursor)
        cursor -= timedelta(days=1)
    return list(reversed(days))


def upsert_history() -> None:
    db = SessionLocal()
    inserted = 0
    updated = 0
    try:
        for index, observation_date in enumerate(business_days(270)):
            # Smooth but non-flat daily moves provide a transparent, repeatable
            # demo history without representing real market data.
            common_rate_move = 0.00042 * sin(index * 0.41) + 0.00018 * sin(index * 0.11)
            for tenor, (series_id, base_yield) in RATE_FACTORS.items():
                value = base_yield + common_rate_move * (1 + tenor / 35) + 0.018 * sin(index * 0.07 + tenor)
                row = db.query(YieldCurvePoint).filter_by(
                    observation_date=observation_date, tenor_years=tenor, source="DEMO"
                ).first()
                if row:
                    row.yield_percent = value
                    row.series_id = series_id
                    updated += 1
                else:
                    db.add(YieldCurvePoint(
                        observation_date=observation_date,
                        tenor_years=tenor,
                        yield_percent=value,
                        series_id=series_id,
                        source="DEMO",
                    ))
                    inserted += 1

            for spread_type, (series_id, base_spread) in SPREAD_FACTORS.items():
                value = base_spread + 3.4 * sin(index * 0.29) + 1.1 * sin(index * 0.08 + len(spread_type))
                row = db.query(CreditSpread).filter_by(
                    observation_date=observation_date, spread_type=spread_type, source="DEMO"
                ).first()
                if row:
                    row.spread_bps = value
                    row.series_id = series_id
                    updated += 1
                else:
                    db.add(CreditSpread(
                        observation_date=observation_date,
                        spread_type=spread_type,
                        spread_bps=value,
                        series_id=series_id,
                        source="DEMO",
                    ))
                    inserted += 1
        db.commit()
        print(f"Demo history ready: {inserted} inserted, {updated} updated.")
    finally:
        db.close()


if __name__ == "__main__":
    upsert_history()
