from __future__ import annotations

from typing import Optional

from app.embeddings.base_embedding import BaseEmbedding
from app.embeddings.config import EmbeddingConfig
from app.embeddings.embedding_registry import EmbeddingRegistry


class VoyageEmbedding(BaseEmbedding):
    """Voyage AI embedding provider (future implementation).

    Planned models: voyage-2, voyage-large-2, voyage-code-2.
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self._config = config or EmbeddingConfig()
        self._model = self._config.model

    def initialize(self) -> None:
        raise NotImplementedError("VoyageEmbedding is not yet implemented")

    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError("VoyageEmbedding is not yet implemented")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("VoyageEmbedding is not yet implemented")

    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError("VoyageEmbedding is not yet implemented")

    def dimension(self) -> int:
        dimensions = {
            "voyage-2": 1024,
            "voyage-large-2": 1536,
            "voyage-code-2": 1536,
            "voyage-law-2": 1024,
            "voyage-healthcare-2": 1024,
        }
        return dimensions.get(self._model, 1024)

    def model_name(self) -> str:
        return self._model

    def provider_name(self) -> str:
        return "voyage"

    def health_check(self) -> dict:
        return {"status": "error", "error": "Not implemented"}


EmbeddingRegistry.register("voyage", VoyageEmbedding)
