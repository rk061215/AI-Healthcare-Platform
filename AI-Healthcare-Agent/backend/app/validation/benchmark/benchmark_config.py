from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BenchmarkConfig:
    name: str = "default_benchmark"
    description: str = ""
    dataset_name: str = ""
    dataset_path: str = ""

    top_k: int = 5
    k_values: list[int] = field(default_factory=lambda: [1, 3, 5, 10])

    num_warmup_runs: int = 2
    num_benchmark_runs: int = 5
    max_questions: Optional[int] = None

    measure_latency: bool = True
    measure_memory: bool = True
    measure_tokens: bool = True

    rag_enabled: bool = True
    agent_enabled: bool = True
    memory_enabled: bool = False
    tools_enabled: bool = False

    similarity_threshold: float = 0.7
    hallucination_threshold: float = 0.15

    output_dir: str = "benchmark_results"
    save_history: bool = True

    seed: int = 42

    def dict(self) -> dict:
        return {
            "name": self.name,
            "dataset_name": self.dataset_name,
            "top_k": self.top_k,
            "k_values": self.k_values,
            "num_runs": self.num_benchmark_runs,
            "measure_latency": self.measure_latency,
            "measure_memory": self.measure_memory,
            "measure_tokens": self.measure_tokens,
        }
