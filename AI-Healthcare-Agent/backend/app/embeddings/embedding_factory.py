from __future__ import annotations

from typing import Optional

from app.embeddings.base_embedding import BaseEmbedding
from app.embeddings.config import EmbeddingConfig
from app.embeddings.embedding_registry import EmbeddingRegistry
from app.embeddings.exceptions import (
    ConfigurationError,
    ProviderNotFoundError,
)

# Ensure embedding provider implementations are imported so they
# self-register with EmbeddingRegistry (e.g. GeminiEmbedding at
# gemini_embedding.py:111).  Direct imports of embedding_service.py
# bypass app/embeddings/__init__.py, so we need the explicit import here.
from app.embeddings import providers as _embedding_providers  # noqa: F401


class EmbeddingFactory:
    """Configuration-driven factory for embedding providers.

    Usage:
        provider = EmbeddingFactory.create()
        provider = EmbeddingFactory.create(provider_name="openai")
        provider = EmbeddingFactory.create(config=my_config)
    """

    @staticmethod
    def create(
        provider_name: Optional[str] = None,
        config: Optional[EmbeddingConfig] = None,
    ) -> BaseEmbedding:
        resolved = config or EmbeddingConfig()

        name = (provider_name or resolved.provider).lower()

        provider_cls = EmbeddingRegistry.get(name)
        if provider_cls is None:
            raise ProviderNotFoundError(
                f"Embedding provider '{name}' is not registered. "
                f"Available providers: {', '.join(EmbeddingRegistry.list_providers()) or 'none'}"
            )

        try:
            provider = provider_cls(config=resolved)
        except Exception as e:
            raise ConfigurationError(
                f"Failed to instantiate embedding provider '{name}': {e}"
            ) from e

        provider.initialize()
        return provider
