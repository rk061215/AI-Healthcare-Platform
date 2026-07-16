from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RAGEngineConfig:
    provider: str = "gemini"
    model: str = ""
    temperature: float = 0.3
    max_tokens: int = 2048
    top_k: int = 10
    min_score: float = 0.0
    enable_query_classification: bool = True
    enable_query_rewriting: bool = False
    enable_guardrails_pre: bool = True
    enable_guardrails_post: bool = True
    enable_citations: bool = True
    retrieval_provider: str = "vector_retriever"
    context_max_tokens: int = 4000
    context_strategy: str = "priority_truncation"
    prompt_library_path: str = ""
    prompt_rag_response: str = "rag/document_retrieval"
    prompt_generation: str = "chat/patient_chat"
    priority_sections: tuple[str, ...] = (
        "diagnosis", "medication", "assessment", "plan",
    )

    def __post_init__(self) -> None:
        if not self.model:
            self.model = "gemini-2.0-flash"
