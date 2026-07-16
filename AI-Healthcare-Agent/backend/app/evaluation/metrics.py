from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class MetricResult:
    metric_name: str
    score: float
    category: str = "general"
    details: dict[str, Any] = field(default_factory=dict)
    num_samples: int = 0
    passed: bool = True
    error: Optional[str] = None


class Metric(ABC):
    def __init__(self, name: str, category: str = "general") -> None:
        self._name = name
        self._category = category

    @property
    def name(self) -> str:
        return self._name

    @property
    def category(self) -> str:
        return self._category

    @abstractmethod
    def evaluate(self, **kwargs: Any) -> MetricResult:
        ...

    def __call__(self, **kwargs: Any) -> MetricResult:
        return self.evaluate(**kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self._name!r}, category={self._category!r})"


class MetricRegistry:
    def __init__(self) -> None:
        self._metrics: dict[str, Metric] = {}

    def register(self, metric: Metric) -> None:
        if metric.name in self._metrics:
            raise ValueError(f"Metric '{metric.name}' is already registered")
        self._metrics[metric.name] = metric

    def unregister(self, name: str) -> None:
        self._metrics.pop(name, None)

    def get(self, name: str) -> Optional[Metric]:
        return self._metrics.get(name)

    def list_metrics(self, category: Optional[str] = None) -> list[Metric]:
        if category is None:
            return list(self._metrics.values())
        return [m for m in self._metrics.values() if m.category == category]

    def clear(self) -> None:
        self._metrics.clear()

    def evaluate_all(self, **kwargs: Any) -> list[MetricResult]:
        return [metric.evaluate(**kwargs) for metric in self._metrics.values()]


_global_registry = MetricRegistry()


def get_global_registry() -> MetricRegistry:
    return _global_registry


def register_metric(metric: Metric) -> None:
    _global_registry.register(metric)
