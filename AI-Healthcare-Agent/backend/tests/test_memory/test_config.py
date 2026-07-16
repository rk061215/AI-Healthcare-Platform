from __future__ import annotations

from app.memory.config import MemoryConfig


class TestMemoryConfig:
    def test_default_config(self) -> None:
        config = MemoryConfig()
        assert config.provider == "in_memory"
        assert config.default_ttl_seconds == 1800
        assert config.max_memories_per_session == 100
        assert config.max_conversation_turns == 50
        assert config.enable_conversation_memory is True
        assert config.enable_document_context is True
        assert config.enable_pruning is True
        assert config.retention_days == 30

    def test_custom_config(self) -> None:
        config = MemoryConfig(
            provider="redis",
            default_ttl_seconds=3600,
            max_memories_per_session=50,
            enable_pruning=False,
        )
        assert config.provider == "redis"
        assert config.default_ttl_seconds == 3600
        assert config.max_memories_per_session == 50
        assert config.enable_pruning is False

    def test_max_memories_clamped(self) -> None:
        config = MemoryConfig(max_memories_per_session=0)
        assert config.max_memories_per_session == 100
