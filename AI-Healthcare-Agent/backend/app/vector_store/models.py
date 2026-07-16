from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

VECTOR_STORE_SCHEMA_VERSION = "1.0.0"


class IndexableDocument(BaseModel):
    """A document ready for indexing into a vector store.

    All metadata fields are vector-database agnostic.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    embedding: list[float]
    document_type: str = "unknown"
    patient_id: Optional[str] = None
    report_id: Optional[str] = None
    section: Optional[str] = None
    page: Optional[int] = None
    chunk_index: int = 0
    document_version: str = "1.0.0"
    schema_version: str = VECTOR_STORE_SCHEMA_VERSION
    embedding_version: str = ""
    source: str = "ocr"
    language: str = "en"
    provider: str = "unknown"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    extra: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    """Result from a vector store search operation."""

    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    score: float
    metadata: dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[list[float]] = None

    @property
    def patient_id(self) -> Optional[str]:
        return self.metadata.get("patient_id")

    @property
    def report_id(self) -> Optional[str]:
        return self.metadata.get("report_id")

    @property
    def document_type(self) -> Optional[str]:
        return self.metadata.get("document_type")

    @property
    def section(self) -> Optional[str]:
        return self.metadata.get("section")


class CollectionInfo(BaseModel):
    """Information about a vector store collection."""

    model_config = ConfigDict(extra="forbid")

    name: str
    dimension: int
    count: int
    distance_function: str = "cosine"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchFilter(BaseModel):
    """Filter parameters for vector store searches."""

    model_config = ConfigDict(extra="forbid")

    patient_id: Optional[str] = None
    report_id: Optional[str] = None
    document_type: Optional[str] = None
    section: Optional[str] = None
    source: Optional[str] = None
    language: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_chroma_filter(self) -> dict[str, Any]:
        """Convert to ChromaDB metadata filter dict."""
        f: dict[str, Any] = {}
        if self.patient_id:
            f["patient_id"] = self.patient_id
        if self.report_id:
            f["report_id"] = self.report_id
        if self.document_type:
            f["document_type"] = self.document_type
        if self.section:
            f["section"] = self.section
        if self.source:
            f["source"] = self.source
        if self.language:
            f["language"] = self.language
        for k, v in self.metadata.items():
            f[k] = v
        return f
