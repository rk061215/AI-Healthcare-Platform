from __future__ import annotations

from unittest.mock import MagicMock

from app.langgraph.config import LangGraphConfig
from app.langgraph.graph_context import GraphContext
from app.langgraph.graph_state import GraphState


class TestGraphContext:
    def test_default_creation(self):
        config = LangGraphConfig(graph_name="test")
        state = GraphState(graph_name="test")
        ctx = GraphContext(config=config, state=state)
        assert ctx.config.graph_name == "test"
        assert ctx.state.graph_name == "test"

    def test_get_memory_creates_default(self):
        ctx = GraphContext(
            config=LangGraphConfig(),
            state=GraphState(),
        )
        mem = ctx.get_memory()
        assert mem is not None

    def test_populate_services_adds_all_provided(self):
        config = LangGraphConfig(graph_name="test")
        state = GraphState(graph_name="test")
        ctx = GraphContext(config=config, state=state)

        ctx.memory_service = MagicMock()
        ctx.agent_executor = MagicMock()
        ctx.tool_service = MagicMock()
        ctx.rag_engine = MagicMock()
        ctx.context_builder = MagicMock()

        ctx.populate_services(state)

        assert state.services.get("memory_service") is ctx.memory_service
        assert state.services.get("agent_executor") is ctx.agent_executor
        assert state.services.get("tool_service") is ctx.tool_service
        assert state.services.get("rag_engine") is ctx.rag_engine
        assert state.services.get("context_builder") is ctx.context_builder

    def test_populate_services_skips_none(self):
        config = LangGraphConfig()
        state = GraphState()
        ctx = GraphContext(config=config, state=state, memory_service=None)
        ctx.populate_services(state)
        assert "memory_service" not in state.services

    def test_get_agent_executor_creates_from_agent(self):
        from unittest.mock import MagicMock
        mock_executor = MagicMock()
        ctx = GraphContext(
            config=LangGraphConfig(),
            state=GraphState(),
            agent_executor=mock_executor,
        )
        executor = ctx.get_agent_executor()
        assert executor is not None
        assert executor is mock_executor

    def test_get_tool_service_creates_default(self):
        ctx = GraphContext(
            config=LangGraphConfig(),
            state=GraphState(),
        )
        svc = ctx.get_tool_service()
        assert svc is not None
