import yfinance as yf
from datetime import date
from typing import List, Dict, Any
from app.data.base_provider import MarketDataProvider
import pandas as pd

class YFinanceProvider(MarketDataProvider):
    def fetch_historical_prices(self, symbol: str, start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        ticker = yf.Ticker(symbol)
        
        kwargs = {}
        if start_date:
            kwargs['start'] = start_date.strftime("%Y-%m-%d")
        if end_date:
            kwargs['end'] = end_date.strftime("%Y-%m-%d")
            
        if not kwargs:
            kwargs['period'] = "max"
            
        df = ticker.history(**kwargs)
        
        if df.empty:
            return []
            
        records = []
        for dt, row in df.iterrows():
            record = {
                "observation_date": dt.date(),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else None,
                "adjusted_close": None, # yfinance already adjusts by default, can keep None or mapping
                "source": "yfinance"
            }
            records.append(record)
            
        return records
