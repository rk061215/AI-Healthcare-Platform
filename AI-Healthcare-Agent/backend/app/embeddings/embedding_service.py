from __future__ import annotations

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from app.embeddings.base_embedding import BaseEmbedding
from app.embeddings.config import EmbeddingConfig
from app.embeddings.embedding_factory import EmbeddingFactory
from app.embeddings.exceptions import (
    BatchEmbeddingError,
    EmbeddingFailureError,
)
from app.embeddings.schemas import (
    EMBEDDING_SCHEMA_VERSION,
    EMBEDDING_VERSION_INITIAL,
    EmbeddingMetadata,
    EmbeddingVersionInfo,
    MigrationResult,
    OutdatedEmbedding,
    ReEmbeddingResult,
)


class EmbeddingService:
    """High-level embedding service.

    Provides embedding operations with metadata tracking,
    batch processing, and configuration-driven provider selection.
    """

    def __init__(
        self,
        provider: Optional[BaseEmbedding] = None,
        config: Optional[EmbeddingConfig] = None,
    ):
        self._config = config or EmbeddingConfig()
        self._provider = provider or EmbeddingFactory.create(config=self._config)
        self._schema_version = EMBEDDING_SCHEMA_VERSION
        self._embedding_version = EMBEDDING_VERSION_INITIAL

    def embed(self, text: str) -> tuple[list[float], EmbeddingMetadata]:
        start = time.perf_counter()
        vector = self._provider.embed_text(text)
        elapsed = (time.perf_counter() - start) * 1000
        meta = self._build_metadata(duration_ms=round(elapsed, 2))
        return vector, meta

    def embed_batch(
        self, texts: list[str]
    ) -> tuple[list[list[float]], list[EmbeddingMetadata]]:
        if not texts:
            return [], []

        start = time.perf_counter()
        try:
            vectors = self._provider.embed_batch(texts)
        except Exception as e:
            raise BatchEmbeddingError(f"Batch embedding failed: {e}") from e

        elapsed = (time.perf_counter() - start) * 1000
        duration_per = round(elapsed / len(texts), 2) if texts else 0
        metas = [self._build_metadata(duration_ms=duration_per) for _ in texts]
        return vectors, metas

    def embed_query(self, text: str) -> tuple[list[float], EmbeddingMetadata]:
        start = time.perf_counter()
        vector = self._provider.embed_query(text)
        elapsed = (time.perf_counter() - start) * 1000
        meta = self._build_metadata(duration_ms=round(elapsed, 2))
        return vector, meta

    def get_version_info(self) -> EmbeddingVersionInfo:
        return EmbeddingVersionInfo(
            embedding_version=self._embedding_version,
            schema_version=self._schema_version,
            provider=self._provider.provider_name(),
            model=self._provider.model_name(),
            dimensions=self._provider.dimension(),
        )

    def health_check(self) -> dict:
        return self._provider.health_check()

    @property
    def provider(self) -> BaseEmbedding:
        return self._provider

    def _build_metadata(self, duration_ms: Optional[float] = None) -> EmbeddingMetadata:
        return EmbeddingMetadata(
            provider=self._provider.provider_name(),
            model=self._provider.model_name(),
            dimensions=self._provider.dimension(),
            embedding_version=self._embedding_version,
            schema_version=self._schema_version,
            duration_ms=duration_ms,
        )


class ReEmbeddingService(ABC):
    """Abstract interface for detecting and performing re-embedding.

    Responsibilities:
    - Detect chunks with outdated embeddings
    - Queue re-embedding jobs
    - Track embedding and schema versions
    - Support schema migration
    """

    @abstractmethod
    def detect_outdated(
        self,
        chunks: list[dict],
        current_embedding_version: int,
        current_schema_version: str,
    ) -> list[OutdatedEmbedding]:
        """Compare chunk metadata against current versions and return outdated entries."""

    @abstractmethod
    def reembed(
        self,
        chunks: list[dict],
        embedding_service: EmbeddingService,
    ) -> ReEmbeddingResult:
        """Recompute embeddings for the given chunks using the provided service."""

    @abstractmethod
    def get_version_info(self) -> EmbeddingVersionInfo:
        """Return the current embedding versioning state."""

    @abstractmethod
    def migrate_schema(
        self,
        chunks: list[dict],
        target_schema_version: str,
    ) -> MigrationResult:
        """Update embedding metadata schema without recomputing vectors."""
