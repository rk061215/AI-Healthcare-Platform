from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

EMBEDDING_SCHEMA_VERSION = "1.0"
EMBEDDING_VERSION_INITIAL = 1


class EmbeddingMetadata(BaseModel):
    """Metadata recorded alongside every embedding vector.

    Tracks provenance, versioning, and schema information
    to enable re-embedding detection and migration.
    """

    provider: str
    model: str
    dimensions: int
    embedding_version: int = EMBEDDING_VERSION_INITIAL
    schema_version: str = EMBEDDING_SCHEMA_VERSION
    document_version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[float] = None


class OutdatedEmbedding(BaseModel):
    """Describes an embedding that needs re-computation."""

    chunk_id: str
    reason: str
    current_embedding_version: int
    target_embedding_version: int
    current_schema_version: str
    target_schema_version: str
    document_version: int
    latest_document_version: int


class ReEmbeddingResult(BaseModel):
    """Result of a re-embedding operation."""

    total_chunks: int
    succeeded: int
    failed: int
    errors: list[str] = Field(default_factory=list)


class EmbeddingVersionInfo(BaseModel):
    """Current state of the embedding versioning system."""

    embedding_version: int = EMBEDDING_VERSION_INITIAL
    schema_version: str = EMBEDDING_SCHEMA_VERSION
    provider: str = ""
    model: str = ""
    dimensions: int = 0


class MigrationResult(BaseModel):
    """Result of a schema migration operation."""

    previous_schema_version: str
    target_schema_version: str
    chunks_migrated: int
    chunks_failed: int
    errors: list[str] = Field(default_factory=list)
