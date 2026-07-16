from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

RAG_SCHEMA_VERSION = "1.0.0"


class QueryClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_type: str = "unknown"
    confidence: float = 1.0
    sub_questions: list[str] = Field(default_factory=list)
    requires_patient_context: bool = True
    requires_recent_docs: bool = False
    suggested_top_k: int = 10
    suggested_sections: list[str] = Field(default_factory=list)


class ProcessedQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original: str
    normalized: str
    cleaned: str
    language: str = "en"
    is_empty: bool = False
    word_count: int = 0
    has_medical_terms: bool = False
    detected_entities: list[str] = Field(default_factory=list)


class RewrittenQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original: str
    rewritten: str
    expansions: list[str] = Field(default_factory=list)
    strategy: str = "none"


class RAGContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context: str = ""
    fragments: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    total_tokens: int = 0
    fragment_count: int = 0
    has_sufficient_context: bool = False
    build_time_ms: float = 0.0
    conversation_history: str = ""


class GuardrailResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool = True
    score: float = 1.0
    warnings: list[str] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)
    requires_human_review: bool = False


class CitationEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citation_id: int
    document_id: str
    report_id: Optional[str] = None
    chunk_id: str
    page: Optional[int] = None
    section: Optional[str] = None
    source: str = "ocr"
    text_snippet: str = ""
    score: float = 0.0


class CitationBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citations: list[CitationEntry] = Field(default_factory=list)
    formatted_block: str = ""
    citation_count: int = 0


class RAGResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = ""
    citations: CitationBlock = Field(default_factory=CitationBlock)
    query: str = ""
    query_type: str = "unknown"
    guardrail_result: GuardrailResult = Field(default_factory=GuardrailResult)
    processing_time_ms: float = 0.0
    model: str = ""
    provider: str = ""
    schema_version: str = RAG_SCHEMA_VERSION
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RAGRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    patient_id: Optional[str] = None
    report_id: Optional[str] = None
    document_type: Optional[str] = None
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    enable_guardrails: bool = True
    enable_citations: bool = True
    context_strategy: Optional[str] = None
    metadata_filter: dict[str, Any] = Field(default_factory=dict)
    conversation_history: str = ""


class RAGMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_duration_ms: float = 0.0
    query_processing_ms: float = 0.0
    query_classification_ms: float = 0.0
    retrieval_ms: float = 0.0
    context_build_ms: float = 0.0
    guardrail_pre_ms: float = 0.0
    generation_ms: float = 0.0
    guardrail_post_ms: float = 0.0
    citation_ms: float = 0.0
    num_documents_retrieved: int = 0
    num_fragments_in_context: int = 0
    num_citations: int = 0
    retrieval_provider: str = ""
    llm_provider: str = ""
    query_type: str = "unknown"
    truncated: bool = False
    guardrails_triggered: bool = False
