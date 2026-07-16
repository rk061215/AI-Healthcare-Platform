from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.evaluation.metrics import MetricResult

RunResults = dict[str, list[MetricResult]]


@dataclass
class BenchmarkResults:
    benchmark_name: str
    benchmark_version: str
    dataset_name: str
    num_samples: int
    retrieval_results: list[MetricResult] = field(default_factory=list)
    rag_results: list[MetricResult] = field(default_factory=list)
    hallucination_results: list[MetricResult] = field(default_factory=list)
    citation_results: list[MetricResult] = field(default_factory=list)
    performance_results: list[MetricResult] = field(default_factory=list)
    token_usage_results: list[MetricResult] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    num_runs: int = 1
    all_runs: list[RunResults] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
