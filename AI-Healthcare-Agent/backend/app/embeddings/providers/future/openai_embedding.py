from __future__ import annotations

from typing import Optional

from app.embeddings.base_embedding import BaseEmbedding
from app.embeddings.config import EmbeddingConfig
from app.embeddings.embedding_registry import EmbeddingRegistry


class OpenAIEmbedding(BaseEmbedding):
    """OpenAI embedding provider (future implementation).

    Planned model: text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002.
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self._config = config or EmbeddingConfig()
        self._model = self._config.model
        self._client = None

    def initialize(self) -> None:
        raise NotImplementedError("OpenAIEmbedding is not yet implemented")

    def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError("OpenAIEmbedding is not yet implemented")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("OpenAIEmbedding is not yet implemented")

    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError("OpenAIEmbedding is not yet implemented")

    def dimension(self) -> int:
        dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return dimensions.get(self._model, 1536)

    def model_name(self) -> str:
        return self._model

    def provider_name(self) -> str:
        return "openai"

    def health_check(self) -> dict:
        return {"status": "error", "error": "Not implemented"}


EmbeddingRegistry.register("openai", OpenAIEmbedding)
