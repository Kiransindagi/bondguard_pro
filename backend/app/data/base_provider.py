from abc import ABC, abstractmethod
from datetime import date
from typing import Any


class MarketDataProvider(ABC):
    @abstractmethod
    def fetch_historical_prices(self, symbol: str, start_date: date | None = None, end_date: date | None = None) -> list[dict[str, Any]]:
        pass
