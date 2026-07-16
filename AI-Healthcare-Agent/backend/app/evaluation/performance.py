from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.evaluation.latency import LatencyTracker
from app.evaluation.metrics import Metric, MetricResult


@dataclass
class PerformanceReport:
    total_time_seconds: float = 0.0
    operations: dict[str, dict[str, float]] = field(default_factory=dict)
    throughput_per_second: float = 0.0
    num_operations: int = 0
    error_count: int = 0
    details: dict[str, Any] = field(default_factory=dict)


class PerformanceAnalyzer:
    def __init__(self) -> None:
        self._tracker = LatencyTracker()

    @property
    def tracker(self) -> LatencyTracker:
        return self._tracker

    def analyze(self) -> PerformanceReport:
        summary = self._tracker.summary()
        total_time = sum(
            stats.get("total", 0.0) for stats in summary.values()
        )
        total_ops = sum(
            stats.get("count", 0) for stats in summary.values()
        )
        error_count = sum(
            1 for m in self._tracker.get_measurements() if not m.success
        )
        throughput = total_ops / total_time if total_time > 0 else 0.0
        return PerformanceReport(
            total_time_seconds=total_time,
            operations=summary,
            throughput_per_second=throughput,
            num_operations=total_ops,
            error_count=error_count,
        )

    def clear(self) -> None:
        self._tracker.clear()


class PerformanceMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Performance", category="performance")

    def evaluate(
        self,
        analyzer: Optional[PerformanceAnalyzer] = None,
        **kwargs: Any,
    ) -> MetricResult:
        if analyzer is None:
            return MetricResult(
                metric_name=self._name,
                score=0.0,
                category=self._category,
                details={"error": "No PerformanceAnalyzer provided"},
                passed=False,
            )
        report = analyzer.analyze()
        return MetricResult(
            metric_name=self._name,
            score=report.throughput_per_second,
            category=self._category,
            details={
                "total_time_seconds": report.total_time_seconds,
                "throughput_per_second": report.throughput_per_second,
                "num_operations": report.num_operations,
                "error_count": report.error_count,
                "operations": report.operations,
            },
            num_samples=report.num_operations,
        )


def compute_operation_stats(
    times: list[float],
) -> dict[str, float]:
    if not times:
        return {}
    sorted_times = sorted(times)
    n = len(sorted_times)
    return {
        "min": sorted_times[0],
        "max": sorted_times[-1],
        "avg": sum(sorted_times) / n,
        "median": sorted_times[n // 2],
        "p95": sorted_times[int(n * 0.95)],
        "p99": sorted_times[int(n * 0.99)],
        "count": n,
        "total": sum(sorted_times),
    }
