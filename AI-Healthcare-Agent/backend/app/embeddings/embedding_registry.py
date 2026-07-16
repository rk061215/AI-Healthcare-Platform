from __future__ import annotations

from typing import Optional, Type

from app.embeddings.base_embedding import BaseEmbedding


class EmbeddingRegistry:
    """Registry of embedding provider classes.

    Providers self-register via register() at import time.
    Factory uses this to look up providers by name.
    """

    _providers: dict[str, Type[BaseEmbedding]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[BaseEmbedding]) -> None:
        cls._providers[name.lower()] = provider_cls

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseEmbedding]]:
        return cls._providers.get(name.lower())

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())

    @classmethod
    def unregister(cls, name: str) -> None:
        cls._providers.pop(name.lower(), None)

    @classmethod
    def clear(cls) -> None:
        cls._providers.clear()
