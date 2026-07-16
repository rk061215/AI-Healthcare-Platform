from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Generator, Optional

from app.evaluation.metrics import Metric, MetricResult


@dataclass
class LatencyMeasurement:
    operation: str
    start_time: float
    end_time: float
    duration_seconds: float
    success: bool = True
    details: dict[str, Any] = field(default_factory=dict)


class LatencyTracker:
    def __init__(self) -> None:
        self._measurements: list[LatencyMeasurement] = []
        self._current: Optional[LatencyMeasurement] = None

    @contextmanager
    def measure(self, operation: str) -> Generator[None, None, None]:
        start = time.time()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            end = time.time()
            measurement = LatencyMeasurement(
                operation=operation,
                start_time=start,
                end_time=end,
                duration_seconds=end - start,
                success=success,
            )
            self._measurements.append(measurement)

    def record(
        self,
        operation: str,
        duration_seconds: float,
        success: bool = True,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        now = time.time()
        measurement = LatencyMeasurement(
            operation=operation,
            start_time=now - duration_seconds,
            end_time=now,
            duration_seconds=duration_seconds,
            success=success,
            details=details or {},
        )
        self._measurements.append(measurement)

    def get_measurements(self, operation: Optional[str] = None) -> list[LatencyMeasurement]:
        if operation is None:
            return list(self._measurements)
        return [m for m in self._measurements if m.operation == operation]

    def clear(self) -> None:
        self._measurements.clear()

    def summary(self) -> dict[str, dict[str, float]]:
        ops: dict[str, list[float]] = {}
        for m in self._measurements:
            if m.success:
                ops.setdefault(m.operation, []).append(m.duration_seconds)
        result: dict[str, dict[str, float]] = {}
        for op, durations in ops.items():
            if durations:
                result[op] = {
                    "min": min(durations),
                    "max": max(durations),
                    "avg": sum(durations) / len(durations),
                    "median": sorted(durations)[len(durations) // 2],
                    "count": len(durations),
                    "total": sum(durations),
                    "p95": _percentile(sorted(durations), 95),
                    "p99": _percentile(sorted(durations), 99),
                }
        return result


def _percentile(sorted_data: list[float], percentile: float) -> float:
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * percentile / 100.0
    f = int(k)
    c = f + 1 if f + 1 < len(sorted_data) else f
    if c == f:
        return sorted_data[f]
    return sorted_data[f] * (c - k) + sorted_data[c] * (k - f)


class LatencyMetric(Metric):
    def __init__(self, operation: str = "total") -> None:
        super().__init__(name=f"Latency ({operation})", category="performance")
        self._operation = operation

    def evaluate(
        self,
        tracker: Optional[LatencyTracker] = None,
        **kwargs: Any,
    ) -> MetricResult:
        if tracker is None:
            return MetricResult(
                metric_name=self._name,
                score=0.0,
                category=self._category,
                details={"error": "No LatencyTracker provided"},
                passed=False,
            )
        summary = tracker.summary()
        op_stats = summary.get(self._operation, {})
        if not op_stats:
            return MetricResult(
                metric_name=self._name,
                score=0.0,
                category=self._category,
                details={"error": f"No measurements for '{self._operation}'"},
                passed=False,
            )
        return MetricResult(
            metric_name=self._name,
            score=op_stats.get("avg", 0.0),
            category=self._category,
            details={
                "operation": self._operation,
                "avg_seconds": op_stats.get("avg", 0.0),
                "min_seconds": op_stats.get("min", 0.0),
                "max_seconds": op_stats.get("max", 0.0),
                "median_seconds": op_stats.get("median", 0.0),
                "p95_seconds": op_stats.get("p95", 0.0),
                "p99_seconds": op_stats.get("p99", 0.0),
                "count": op_stats.get("count", 0),
                "total_seconds": op_stats.get("total", 0.0),
            },
            num_samples=op_stats.get("count", 0),
        )
