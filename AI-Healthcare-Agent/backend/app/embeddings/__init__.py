"""Provider-independent embedding layer.

Architecture:
    BaseEmbedding (ABC) ← GeminiEmbedding, OpenAIEmbedding, ...
    EmbeddingRegistry — maps provider names to classes
    EmbeddingFactory — configuration-driven instantiation
    EmbeddingService — high-level API with metadata tracking
    ReEmbeddingService (ABC) — interface for version management
"""

from app.embeddings.base_embedding import BaseEmbedding
from app.embeddings.config import EmbeddingConfig
from app.embeddings.embedding_factory import EmbeddingFactory
from app.embeddings.embedding_registry import EmbeddingRegistry
from app.embeddings.embedding_service import EmbeddingService, ReEmbeddingService
from app.embeddings.schemas import (
    EMBEDDING_SCHEMA_VERSION,
    EmbeddingMetadata,
    EmbeddingVersionInfo,
    MigrationResult,
    OutdatedEmbedding,
    ReEmbeddingResult,
)

__all__ = [
    "BaseEmbedding",
    "EmbeddingConfig",
    "EmbeddingFactory",
    "EmbeddingRegistry",
    "EmbeddingService",
    "ReEmbeddingService",
    "EmbeddingMetadata",
    "EmbeddingVersionInfo",
    "OutdatedEmbedding",
    "ReEmbeddingResult",
    "MigrationResult",
    "EMBEDDING_SCHEMA_VERSION",
]
