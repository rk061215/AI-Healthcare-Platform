from __future__ import annotations

from typing import Type

from app.vector_store.base_vector_store import BaseVectorStore
from app.vector_store.exceptions import ProviderNotFoundError


class VectorStoreRegistry:
    """Global registry mapping provider names to BaseVectorStore classes."""

    _providers: dict[str, Type[BaseVectorStore]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[BaseVectorStore]) -> None:
        """Register a vector store provider class."""
        cls._providers[name] = provider_cls

    @classmethod
    def get(cls, name: str) -> Type[BaseVectorStore]:
        """Get a registered provider class by name."""
        if name not in cls._providers:
            raise ProviderNotFoundError(
                f"Vector store provider '{name}' is not registered. "
                f"Available: {list(cls._providers.keys())}"
            )
        return cls._providers[name]

    @classmethod
    def list_providers(cls) -> list[str]:
        """List all registered provider names."""
        return list(cls._providers.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered providers (primarily for testing)."""
        cls._providers.clear()

    @classmethod
    def __contains__(cls, name: str) -> bool:
        return name in cls._providers

    @classmethod
    def _save_registry(cls) -> dict[str, Type[BaseVectorStore]]:
        """Return a copy of the current registry (for test isolation)."""
        return dict(cls._providers)

    @classmethod
    def _restore_registry(cls, saved: dict[str, Type[BaseVectorStore]]) -> None:
        """Restore a previously saved registry state."""
        cls._providers = dict(saved)
