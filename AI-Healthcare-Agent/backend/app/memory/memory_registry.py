from __future__ import annotations

from typing import Optional

from app.memory.base_memory import BaseMemoryStore


class MemoryRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, type[BaseMemoryStore]] = {}

    def register(self, name: str, provider: type[BaseMemoryStore]) -> None:
        if name in self._providers:
            raise ValueError(f"Memory provider '{name}' is already registered")
        self._providers[name] = provider

    def unregister(self, name: str) -> None:
        self._providers.pop(name, None)

    def get(self, name: str) -> Optional[type[BaseMemoryStore]]:
        return self._providers.get(name)

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    def clear(self) -> None:
        self._providers.clear()


_global_registry = MemoryRegistry()


def get_global_registry() -> MemoryRegistry:
    return _global_registry
