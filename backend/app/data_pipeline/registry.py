from typing import Dict, Any, List

DATASET_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Yield Curve Points (FRED)
    "DGS2": {
        "dataset_key": "DGS2",
        "source": "FRED",
        "category": "Yield_Curve",
        "expected_frequency": "business_daily",
        "unit": "percent",
        "is_active": True,
        "freshness_tolerance": 3,
        "min_observations": 252
    },
    "DGS5": {
        "dataset_key": "DGS5",
        "source": "FRED",
        "category": "Yield_Curve",
        "expected_frequency": "business_daily",
        "unit": "percent",
        "is_active": True,
        "freshness_tolerance": 3,
        "min_observations": 252
    },
    "DGS10": {
        "dataset_key": "DGS10",
        "source": "FRED",
        "category": "Yield_Curve",
        "expected_frequency": "business_daily",
        "unit": "percent",
        "is_active": True,
        "freshness_tolerance": 3,
        "min_observations": 252
    },
    "DGS30": {
        "dataset_key": "DGS30",
        "source": "FRED",
        "category": "Yield_Curve",
        "expected_frequency": "business_daily",
        "unit": "percent",
        "is_active": True,
        "freshness_tolerance": 3,
        "min_observations": 252
    },

    # Credit Spreads (FRED)
    "BAMLC0A0CM": {
        "dataset_key": "BAMLC0A0CM",
        "source": "FRED",
        "category": "Credit_Spreads",
        "expected_frequency": "business_daily",
        "unit": "bps",
        "is_active": True,
        "freshness_tolerance": 3,
        "min_observations": 252
    },
    "BAMLH0A0HYM2": {
        "dataset_key": "BAMLH0A0HYM2",
        "source": "FRED",
        "category": "Credit_Spreads",
        "expected_frequency": "business_daily",
        "unit": "bps",
        "is_active": True,
        "freshness_tolerance": 3,
        "min_observations": 252
    },

    # Macro Observations (FRED)
    "DFF": {
        "dataset_key": "DFF",
        "source": "FRED",
        "category": "Macro",
        "expected_frequency": "daily",
        "unit": "percent",
        "is_active": True,
        "freshness_tolerance": 3,
        "min_observations": 252
    },

    # ETF Context (yfinance)
    "SHY": {
        "dataset_key": "SHY",
        "source": "yfinance",
        "category": "ETF_Market_Data",
        "expected_frequency": "business_daily",
        "unit": "USD",
        "is_active": True,
        "freshness_tolerance": 5,
        "min_observations": 252
    },
    "IEF": {
        "dataset_key": "IEF",
        "source": "yfinance",
        "category": "ETF_Market_Data",
        "expected_frequency": "business_daily",
        "unit": "USD",
        "is_active": True,
        "freshness_tolerance": 5,
        "min_observations": 252
    },
    "TLT": {
        "dataset_key": "TLT",
        "source": "yfinance",
        "category": "ETF_Market_Data",
        "expected_frequency": "business_daily",
        "unit": "USD",
        "is_active": True,
        "freshness_tolerance": 5,
        "min_observations": 252
    },
    "LQD": {
        "dataset_key": "LQD",
        "source": "yfinance",
        "category": "ETF_Market_Data",
        "expected_frequency": "business_daily",
        "unit": "USD",
        "is_active": True,
        "freshness_tolerance": 5,
        "min_observations": 252
    },
    "HYG": {
        "dataset_key": "HYG",
        "source": "yfinance",
        "category": "ETF_Market_Data",
        "expected_frequency": "business_daily",
        "unit": "USD",
        "is_active": True,
        "freshness_tolerance": 5,
        "min_observations": 252
    },
    "EMB": {
        "dataset_key": "EMB",
        "source": "yfinance",
        "category": "ETF_Market_Data",
        "expected_frequency": "business_daily",
        "unit": "USD",
        "is_active": True,
        "freshness_tolerance": 5,
        "min_observations": 252
    }
}

def get_active_datasets() -> List[Dict[str, Any]]:
    return [meta for meta in DATASET_REGISTRY.values() if meta["is_active"]]

def get_dataset_metadata(dataset_key: str) -> Dict[str, Any]:
    return DATASET_REGISTRY.get(dataset_key)
