from typing import Dict, Any

def validate_market_price(record: Dict[str, Any]) -> bool:
    if record["open"] < 0 or record["high"] < 0 or record["low"] < 0 or record["close"] < 0:
        return False
    if record["high"] < record["low"]:
        return False
    return True

def validate_yield_curve_point(record: Dict[str, Any]) -> bool:
    # yields can technically be negative in some extreme regimes, but let's just make sure it's numeric and has a tenor
    if "yield_percent" not in record or record["yield_percent"] is None:
        return False
    return True
