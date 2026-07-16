from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.validation.benchmark.benchmark_config import BenchmarkConfig
from app.validation.benchmark.benchmark_metrics import BenchmarkMetrics


@dataclass
class BenchmarkResult:
    config_name: str
    timestamp: str = ""
    overall_scores: dict[str, float] = field(default_factory=dict)
    per_question_scores: list[dict[str, Any]] = field(default_factory=list)
    latency_stats: dict[str, float] = field(default_factory=dict)
    memory_stats: dict[str, float] = field(default_factory=dict)
    token_stats: dict[str, float] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    questions_attempted: int = 0
    questions_succeeded: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def success_rate(self) -> float:
        if self.questions_attempted == 0:
            return 0.0
        return self.questions_succeeded / self.questions_attempted

    def summary(self) -> dict[str, Any]:
        return {
            "config": self.config_name,
            "timestamp": self.timestamp,
            "questions_attempted": self.questions_attempted,
            "questions_succeeded": self.questions_succeeded,
            "success_rate": self.success_rate(),
            "overall_scores": self.overall_scores,
            "latency_stats": self.latency_stats,
            "memory_stats": self.memory_stats,
            "token_stats": self.token_stats,
            "error_count": len(self.errors),
        }


class BenchmarkSuite:
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.metrics = BenchmarkMetrics()
        self._results: list[BenchmarkResult] = []

    @property
    def results(self) -> list[BenchmarkResult]:
        return list(self._results)

    def add_result(self, result: BenchmarkResult) -> None:
        self._results.append(result)

    def aggregate(self) -> Optional[BenchmarkResult]:
        if not self._results:
            return None
        all_latencies: list[float] = []
        all_tokens: list[float] = []
        all_memories: list[float] = []
        aggregated_scores: dict[str, list[float]] = {}

        for r in self._results:
            for key, val in r.overall_scores.items():
                if key not in aggregated_scores:
                    aggregated_scores[key] = []
                aggregated_scores[key].append(val)
            if r.latency_stats:
                all_latencies.append(r.latency_stats.get("mean", 0))
            if r.token_stats:
                all_tokens.append(r.token_stats.get("total", 0))
            if r.memory_stats:
                all_memories.append(r.memory_stats.get("peak_mb", 0))

        combined = BenchmarkResult(
            config_name=f"{self.config.name}_aggregated",
            questions_attempted=sum(r.questions_attempted for r in self._results),
            questions_succeeded=sum(r.questions_succeeded for r in self._results),
        )
        combined.overall_scores = {
            k: BenchmarkMetrics.mean(v) for k, v in aggregated_scores.items()
        }
        if all_latencies:
            combined.latency_stats = {
                "mean": BenchmarkMetrics.mean(all_latencies),
                "median": BenchmarkMetrics.median(all_latencies),
                "p95": BenchmarkMetrics.percentile(all_latencies, 95),
                "p99": BenchmarkMetrics.percentile(all_latencies, 99),
                "min": min(all_latencies),
                "max": max(all_latencies),
            }
        if all_tokens:
            combined.token_stats = {
                "mean": BenchmarkMetrics.mean(all_tokens),
                "total": sum(all_tokens),
                "min": min(all_tokens),
                "max": max(all_tokens),
            }
        if all_memories:
            combined.memory_stats = {
                "mean_mb": BenchmarkMetrics.mean(all_memories),
                "peak_mb": max(all_memories),
            }
        return combined
