from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvaluationConfig:
    provider: str = "gemini"
    model: str = ""
    temperature: float = 0.3
    top_k: int = 10
    min_score: float = 0.0
    k_values: tuple[int, ...] = (1, 3, 5, 10)
    retrieval_metrics_enabled: bool = True
    rag_metrics_enabled: bool = True
    hallucination_metrics_enabled: bool = True
    citation_metrics_enabled: bool = True
    performance_metrics_enabled: bool = True
    token_usage_metrics_enabled: bool = True
    medical_qa_metrics_enabled: bool = True
    dataset_path: str = "datasets"
    output_path: str = "evaluation_reports"
    report_format: str = "json"
    report_include_raw_data: bool = False
    benchmark_name: str = "default_benchmark"
    benchmark_version: str = "1.0.0"
    num_runs: int = 1
    warmup_runs: int = 0
    timeout_seconds: int = 300
    verbose: bool = False

    def __post_init__(self) -> None:
        if not self.model:
            self.model = "gemini-2.0-flash"
