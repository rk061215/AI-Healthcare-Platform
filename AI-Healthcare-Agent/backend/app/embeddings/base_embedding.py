from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class BaseEmbedding(ABC):
    """Abstract interface for all embedding providers.

    Every embedding provider must implement:
    - embed_text: single text → vector
    - embed_batch: multiple texts → vectors
    - embed_query: query text → vector (may differ from document embedding)
    - dimension: output vector dimensionality
    - model_name: the model string used
    - provider_name: unique provider identifier
    - health_check: verify the provider is operational
    """

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string."""

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Generate an embedding vector optimized for retrieval queries.

        Default implementation delegates to embed_text.
        Providers with separate query/doc models should override this.
        """

    @abstractmethod
    def dimension(self) -> int:
        """Return the dimensionality of the embedding vectors."""

    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier string."""

    @abstractmethod
    def provider_name(self) -> str:
        """Return a unique provider name string (e.g. 'gemini', 'openai')."""

    @abstractmethod
    def health_check(self) -> dict:
        """Verify provider health.

        Returns a dict with at minimum:
            {"status": "ok" | "error", "error": str | None}
        """
