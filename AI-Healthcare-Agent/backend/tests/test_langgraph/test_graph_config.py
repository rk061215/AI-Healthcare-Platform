from __future__ import annotations

from app.langgraph.config import LangGraphConfig


class TestLangGraphConfig:
    def test_default_config(self):
        config = LangGraphConfig()
        assert config.graph_name == "medical_qa"
        assert config.execution_timeout_ms == 60000.0
        assert config.node_timeout_ms == 30000
        assert config.max_retries == 2
        assert config.retry_delay_seconds == 0.5
        assert config.enable_events is True
        assert config.enable_metrics is True
        assert config.enable_checkpointing is True

    def test_custom_config(self):
        config = LangGraphConfig(
            graph_name="custom_graph",
            execution_timeout_ms=60000,
            node_timeout_ms=15000,
            max_retries=3,
        )
        assert config.graph_name == "custom_graph"
        assert config.execution_timeout_ms == 60000
        assert config.node_timeout_ms == 15000
        assert config.max_retries == 3

    def test_disabled_features(self):
        config = LangGraphConfig(
            enable_events=False,
            enable_metrics=False,
            enable_checkpointing=False,
        )
        assert config.enable_events is False
        assert config.enable_metrics is False
        assert config.enable_checkpointing is False
