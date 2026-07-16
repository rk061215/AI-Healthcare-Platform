from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RetrieverConfig:
    provider: str = ""
    top_k: int = 10
    max_retrieval_attempts: int = 2
    min_score_threshold: float = 0.0
    enable_hybrid_search: bool = False
    enable_metadata_filtering: bool = True
    default_search_type: str = "similarity"

    def __post_init__(self) -> None:
        if not self.provider:
            self.provider = "vector_retriever"
