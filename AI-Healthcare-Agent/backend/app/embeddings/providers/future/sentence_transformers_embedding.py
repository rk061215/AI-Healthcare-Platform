from __future__ import annotations

from typing import Optional

from app.embeddings.base_embedding import BaseEmbedding
from app.embeddings.config import EmbeddingConfig
from app.embeddings.embedding_registry import EmbeddingRegistry


class SentenceTransformersEmbedding(BaseEmbedding):
    """Local sentence-transformers embedding provider (future implementation).

    Planned models: all-MiniLM-L6-v2, all-mpnet-base-v2, BAAI/bge-small-en-v1.5.
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self._config = config or EmbeddingConfig()
        self._model = self._config.model

    def initialize(self) -> None:
        raise NotImplementedError("SentenceTransformersEmbedding is not yet implemented")

    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError("SentenceTransformersEmbedding is not yet implemented")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("SentenceTransformersEmbedding is not yet implemented")

    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError("SentenceTransformersEmbedding is not yet implemented")

    def dimension(self) -> int:
        dimensions = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "BAAI/bge-small-en-v1.5": 384,
            "BAAI/bge-base-en-v1.5": 768,
            "BAAI/bge-large-en-v1.5": 1024,
        }
        return dimensions.get(self._model, 384)

    def model_name(self) -> str:
        return self._model

    def provider_name(self) -> str:
        return "sentence_transformers"

    def health_check(self) -> dict:
        return {"status": "error", "error": "Not implemented"}


EmbeddingRegistry.register("sentence_transformers", SentenceTransformersEmbedding)
EmbeddingRegistry.register("sentence-transformers", SentenceTransformersEmbedding)
