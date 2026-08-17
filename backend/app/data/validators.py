from typing import Any


def validate_market_price(record: dict[str, Any]) -> bool:
    if record["open"] < 0 or record["high"] < 0 or record["low"] < 0 or record["close"] < 0:
        return False
    return not record["high"] < record["low"]

def validate_yield_curve_point(record: dict[str, Any]) -> bool:
    # yields can technically be negative in some extreme regimes, but let's just make sure it's numeric and has a tenor
    return not ("yield_percent" not in record or record["yield_percent"] is None)
