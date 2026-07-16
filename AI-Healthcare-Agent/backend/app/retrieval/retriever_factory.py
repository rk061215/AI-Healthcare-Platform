from __future__ import annotations

from typing import Optional

from app.retrieval.base_retriever import BaseRetriever
from app.retrieval.config import RetrieverConfig
from app.retrieval.retriever_registry import RetrieverRegistry


class RetrieverFactory:
    """Configuration-driven retriever provider instantiation."""

    @staticmethod
    def create(
        config: Optional[RetrieverConfig] = None,
    ) -> BaseRetriever:
        cfg = config or RetrieverConfig()
        provider_cls = RetrieverRegistry.get(cfg.provider)
        instance = provider_cls(config=cfg)
        instance.initialize()
        return instance
