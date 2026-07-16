from __future__ import annotations

from typing import Optional

from app.vector_store.base_vector_store import BaseVectorStore
from app.vector_store.config import VectorStoreConfig
from app.vector_store.exceptions import ConfigurationError
from app.vector_store.vector_store_registry import VectorStoreRegistry


class VectorStoreFactory:
    """Configuration-driven vector store provider instantiation."""

    @staticmethod
    def create(
        config: Optional[VectorStoreConfig] = None,
    ) -> BaseVectorStore:
        cfg = config or VectorStoreConfig()
        provider_cls = VectorStoreRegistry.get(cfg.provider)
        instance = provider_cls(config=cfg)
        instance.initialize()
        return instance
