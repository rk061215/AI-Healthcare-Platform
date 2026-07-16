from __future__ import annotations

import pytest

from app.memory.memory_factory import MemoryFactory
from app.memory.memory_registry import MemoryRegistry, get_global_registry
from app.memory.stores.future.redis_store import RedisStore
from app.memory.stores.in_memory_store import InMemoryStore


class TestMemoryRegistry:
    def test_register_and_get(self) -> None:
        registry = MemoryRegistry()
        registry.register("test_provider", InMemoryStore)
        assert registry.get("test_provider") is InMemoryStore

    def test_register_duplicate_raises(self) -> None:
        registry = MemoryRegistry()
        registry.register("dup", InMemoryStore)
        with pytest.raises(ValueError, match="already registered"):
            registry.register("dup", InMemoryStore)

    def test_unregister(self) -> None:
        registry = MemoryRegistry()
        registry.register("tmp", InMemoryStore)
        registry.unregister("tmp")
        assert registry.get("tmp") is None

    def test_list_providers(self) -> None:
        registry = MemoryRegistry()
        registry.register("a", InMemoryStore)
        registry.register("b", InMemoryStore)
        providers = registry.list_providers()
        assert "a" in providers
        assert "b" in providers

    def test_clear(self) -> None:
        registry = MemoryRegistry()
        registry.register("x", InMemoryStore)
        registry.clear()
        assert registry.list_providers() == []

    def test_global_registry(self) -> None:
        registry = get_global_registry()
        assert isinstance(registry, MemoryRegistry)
        assert "in_memory" in registry.list_providers()


class TestMemoryFactory:
    def test_create_in_memory(self) -> None:
        store = MemoryFactory.create("in_memory")
        assert isinstance(store, InMemoryStore)
        assert store.health_check() is True

    def test_create_unknown_provider(self) -> None:
        with pytest.raises(ValueError, match="Unknown memory provider"):
            MemoryFactory.create("nonexistent")
