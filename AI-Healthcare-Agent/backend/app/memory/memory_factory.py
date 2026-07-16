from __future__ import annotations

from app.memory.base_memory import BaseMemoryStore
from app.memory.memory_registry import get_global_registry


class MemoryFactory:
    @staticmethod
    def create(provider: str = "in_memory") -> BaseMemoryStore:
        registry = get_global_registry()
        provider_class = registry.get(provider)
        if provider_class is None:
            raise ValueError(
                f"Unknown memory provider '{provider}'. "
                f"Available providers: {registry.list_providers()}"
            )
        return provider_class()
