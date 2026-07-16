from __future__ import annotations

import pytest

from app.langgraph.config import LangGraphConfig
from app.langgraph.graph_context import GraphContext
from app.langgraph.graph_runtime import BaseGraph
from app.langgraph.graph_state import GraphPhase, GraphState, GraphStatus


class SimpleTestGraph(BaseGraph):
    def build(self) -> None:
        def node_a(state: GraphState) -> GraphState:
            state.context_updates.append("node_a executed")
            return state

        def node_b(state: GraphState) -> GraphState:
            state.final_response = "node_b response"
            state.context_updates.append("node_b executed")
            return state

        self._executor.register_node("node_a", node_a)
        self._executor.register_node("node_b", node_b)

    def _run_pipeline(self, state: GraphState) -> GraphState:
        state = self._executor.execute_node("node_a", state, "phase_a")
        state = self._executor.execute_node("node_b", state, "phase_b")
        return state


class TestBaseGraph:
    def test_initialize_and_build(self):
        graph = SimpleTestGraph(
            config=LangGraphConfig(graph_name="test", enable_events=False, enable_metrics=False, enable_checkpointing=False)
        )
        graph.initialize()
        assert graph._built is True

    def test_execute_returns_completed_state(self):
        graph = SimpleTestGraph(
            config=LangGraphConfig(graph_name="test", enable_events=False, enable_metrics=False, enable_checkpointing=False)
        )
        state = GraphState(query="test query", session_id="sess_1")
        result = graph.execute(state)
        assert result.status == GraphStatus.COMPLETED.value
        assert result.phase == GraphPhase.COMPLETED.value
        assert result.final_response == "node_b response"
        assert result.total_duration_ms > 0

    def test_execute_sets_running_status(self):
        graph = SimpleTestGraph(
            config=LangGraphConfig(graph_name="test", enable_events=False, enable_metrics=False, enable_checkpointing=False)
        )
        graph.initialize()
        assert graph.state.status == GraphStatus.PENDING.value

    def test_checkpoint_returns_id(self):
        graph = SimpleTestGraph(
            config=LangGraphConfig(graph_name="test", enable_events=False, enable_metrics=False, enable_checkpointing=True)
        )
        graph.initialize()
        state = GraphState(query="test", session_id="sess_1")
        graph.execute(state)
        cp_id = graph.checkpoint()
        assert cp_id is not None

    def test_checkpoint_disabled(self):
        graph = SimpleTestGraph(
            config=LangGraphConfig(graph_name="test", enable_checkpointing=False)
        )
        graph.initialize()
        cp_id = graph.checkpoint()
        assert cp_id is None

    def test_shutdown_clears_events(self):
        graph = SimpleTestGraph(
            config=LangGraphConfig(graph_name="test", enable_events=True)
        )
        graph.initialize()
        graph.shutdown()
        assert len(graph.event_bus._handlers) == 0

    def test_properties(self):
        config = LangGraphConfig(graph_name="prop_test")
        graph = SimpleTestGraph(config=config)
        assert graph.config is config
        assert isinstance(graph.state, GraphState)
        assert isinstance(graph.context, GraphContext)
        assert isinstance(graph.executor, graph._executor.__class__)


class TestGraphExecution:
    def test_pipeline_execution_order(self):
        execution_order = []

        def make_node(name: str):
            def node(state: GraphState) -> GraphState:
                execution_order.append(name)
                return state
            return node

        class OrderedGraph(BaseGraph):
            def build(self) -> None:
                self._executor.register_node("first", make_node("first"))
                self._executor.register_node("second", make_node("second"))
                self._executor.register_node("third", make_node("third"))

            def _run_pipeline(self, state: GraphState) -> GraphState:
                state = self._executor.execute_node("first", state, "p1")
                state = self._executor.execute_node("second", state, "p2")
                state = self._executor.execute_node("third", state, "p3")
                return state

        graph = OrderedGraph(
            config=LangGraphConfig(graph_name="ordered", enable_events=False, enable_metrics=False, enable_checkpointing=False)
        )
        graph.execute(GraphState(query="test"))
        assert execution_order == ["first", "second", "third"]
