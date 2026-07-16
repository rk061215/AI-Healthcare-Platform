from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

CONTEXT_SCHEMA_VERSION = "1.0.0"


class CitationInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    report_id: Optional[str] = None
    chunk_id: str
    page: Optional[int] = None
    section: Optional[str] = None
    chunk_index: int = 0
    source: str = "ocr"

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True)


class TokenUsageInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    estimated_tokens: int = 0
    max_allowed_tokens: int = 0
    remaining_tokens: int = 0
    truncated: bool = False
    fragments_count: int = 0
    strategy: str = "fixed_max"


class ContextFragment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    score: float
    citation: CitationInfo
    original_chunk_index: int = 0
    rank: int = 0
    merged: bool = False
    source_fragment_ids: list[str] = Field(default_factory=list)


class BuildContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    fragments: list[ContextFragment]
    max_tokens: int = 4000
    preserve_sections: bool = True
    priority_fields: Optional[list[str]] = None
    include_citations: bool = True
    strategy: str = "fixed_max"


class BuildContextResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context: str = ""
    fragments: list[ContextFragment] = Field(default_factory=list)
    token_usage: TokenUsageInfo = Field(default_factory=TokenUsageInfo)
    citations: list[CitationInfo] = Field(default_factory=list)
    total_fragments_input: int = 0
    fragments_after_dedup: int = 0
    fragments_after_rank: int = 0
    fragments_after_compress: int = 0
    fragments_in_context: int = 0
    dedup_removed: int = 0
    compressed_merged: int = 0
    truncated: bool = False
    build_time_ms: float = 0.0
    schema_version: str = CONTEXT_SCHEMA_VERSION
