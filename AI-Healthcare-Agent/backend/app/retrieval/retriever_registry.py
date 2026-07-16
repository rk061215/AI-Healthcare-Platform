from __future__ import annotations

from typing import Type

from app.retrieval.base_retriever import BaseRetriever
from app.retrieval.exceptions import RetrieverNotFoundError


class RetrieverRegistry:
    """Global registry mapping retriever names to BaseRetriever classes."""

    _providers: dict[str, Type[BaseRetriever]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[BaseRetriever]) -> None:
        cls._providers[name] = provider_cls

    @classmethod
    def get(cls, name: str) -> Type[BaseRetriever]:
        if name not in cls._providers:
            raise RetrieverNotFoundError(
                f"Retriever provider '{name}' is not registered. "
                f"Available: {list(cls._providers.keys())}"
            )
        return cls._providers[name]

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())

    @classmethod
    def clear(cls) -> None:
        cls._providers.clear()

    @classmethod
    def _save_registry(cls) -> dict[str, Type[BaseRetriever]]:
        return dict(cls._providers)

    @classmethod
    def _restore_registry(cls, saved: dict[str, Type[BaseRetriever]]) -> None:
        cls._providers = dict(saved)
