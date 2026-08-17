from enum import Enum


class IngestionStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"

TREASURY_SERIES = {
    "2Y": "DGS2",
    "5Y": "DGS5",
    "10Y": "DGS10",
    "30Y": "DGS30"
}

MACRO_SERIES = {
    "Fed_Funds": "DFF",
    "IG_Spread": "BAMLC0A0CM",
    "HY_Spread": "BAMLH0A0HYM2"
}

ETF_SYMBOLS = ["SHY", "IEF", "TLT", "LQD", "HYG", "EMB"]
