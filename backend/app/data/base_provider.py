from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import date

class MarketDataProvider(ABC):
    @abstractmethod
    def fetch_historical_prices(self, symbol: str, start_date: date = None, end_date: date = None) -> List[Dict[str, Any]]:
        pass
