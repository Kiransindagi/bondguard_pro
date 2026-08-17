from datetime import date
from typing import Any, Protocol

from .enums import MetricType
from .types import NormalizedMetricResult


class MetricAdapter(Protocol):
    def get_value(self, metric: MetricType, portfolio_id: int, valuation_date: date, db: Any) -> NormalizedMetricResult:
        pass

class MetricRegistry:
    def __init__(self):
        self._adapters: dict[MetricType, MetricAdapter] = {}

    def register(self, metric: MetricType, adapter: MetricAdapter):
        self._adapters[metric] = adapter

    def get_adapter(self, metric: MetricType) -> MetricAdapter | None:
        return self._adapters.get(metric)

registry = MetricRegistry()
