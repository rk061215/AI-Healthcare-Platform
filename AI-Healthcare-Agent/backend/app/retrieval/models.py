from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

RETRIEVAL_SCHEMA_VERSION = "1.0.0"


class RetrievalQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    top_k: int = 10
    patient_id: Optional[str] = None
    report_id: Optional[str] = None
    document_type: Optional[str] = None
    section: Optional[str] = None
    source: Optional[str] = None
    language: Optional[str] = None
    metadata_filter: dict[str, Any] = Field(default_factory=dict)
    min_score: float = 0.0
    include_embeddings: bool = False


class RetrievalResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    text: str
    score: float
    document_id: str = ""
    report_id: Optional[str] = None
    patient_id: Optional[str] = None
    document_type: str = "unknown"
    section: Optional[str] = None
    page: Optional[int] = None
    chunk_index: int = 0
    source: str = "ocr"
    language: str = "en"
    embedding: Optional[list[float]] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def citation_id(self) -> str:
        parts = [self.chunk_id]
        if self.report_id:
            parts.append(self.report_id)
        if self.section:
            parts.append(self.section)
        return "/".join(parts)


class RetrievedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: RetrievalQuery
    results: list[RetrievalResult] = Field(default_factory=list)
    total_results: int = 0
    returned_results: int = 0
    retrieval_time_ms: float = 0.0
    provider: str = "unknown"


class RetrievalMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_text_hash: str = ""
    total_chunks_retrieved: int = 0
    chunks_after_filtering: int = 0
    retrieval_duration_ms: float = 0.0
    provider: str = ""
    search_type: str = ""
    filter_applied: bool = False
    patient_filtered: bool = False
    report_filtered: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
