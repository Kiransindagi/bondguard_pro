from typing import List, Dict, Any

# Tenor mapping from series ID to years
TENOR_MAP = {
    "DGS2": 2.0,
    "DGS5": 5.0,
    "DGS10": 10.0,
    "DGS30": 30.0
}

def transform_fred_to_yield_curve(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    transformed = []
    for r in records:
        if r["series_id"] in TENOR_MAP:
            transformed.append({
                "observation_date": r["observation_date"],
                "tenor_years": TENOR_MAP[r["series_id"]],
                "yield_percent": r["value"],
                "series_id": r["series_id"],
                "source": r["source"]
            })
    return transformed

def transform_fred_to_credit_spread(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    transformed = []
    for r in records:
        spread_type = None
        if r["series_id"] == "BAMLC0A0CM":
            spread_type = "IG"
        elif r["series_id"] == "BAMLH0A0HYM2":
            spread_type = "HY"
            
        if spread_type:
            # Credit spreads from FRED are usually in percent (e.g., 1.5 means 1.5% or 150 bps)
            # The instruction says: "store in basis points. Example: 325 means 325 bps."
            # FRED BAML... is in percent. So we multiply by 100.
            transformed.append({
                "observation_date": r["observation_date"],
                "spread_type": spread_type,
                "spread_bps": r["value"] * 100.0,
                "series_id": r["series_id"],
                "source": r["source"]
            })
    return transformed

def transform_fred_to_macro(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    transformed = []
    for r in records:
        metric_name = None
        if r["series_id"] == "DFF":
            metric_name = "Fed_Funds"
            
        if metric_name:
            transformed.append({
                "observation_date": r["observation_date"],
                "metric_name": metric_name,
                "value": r["value"],
                "series_id": r["series_id"],
                "source": r["source"]
            })
    return transformed
