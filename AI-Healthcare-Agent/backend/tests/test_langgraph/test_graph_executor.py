from __future__ import annotations

import pytest

from app.langgraph.exceptions import NodeExecutionError
from app.langgraph.graph_executor import GraphExecutor
from app.langgraph.graph_state import GraphState


class TestGraphExecutor:
    def test_register_and_execute_node(self):
        executor = GraphExecutor()

        def dummy_node(state: GraphState) -> GraphState:
            state.final_response = "hello"
            return state

        executor.register_node("say_hello", dummy_node)
        state = GraphState(query="test")
        result = executor.execute_node("say_hello", state, "test_phase")
        assert result.final_response == "hello"

    def test_execute_unregistered_node(self):
        executor = GraphExecutor()
        with pytest.raises(NodeExecutionError) as excinfo:
            executor.execute_node("nonexistent", GraphState(), "test")
        assert "nonexistent" in str(excinfo.value)

    def test_conditional_edge(self):
        executor = GraphExecutor()

        def route(state: GraphState) -> str:
            return "path_a" if state.need_tool else "path_b"

        executor.register_conditional_edge("router", route)
        state1 = GraphState(need_tool=True)
        assert executor.evaluate_conditional("router", state1) == "path_a"
        state2 = GraphState(need_tool=False)
        assert executor.evaluate_conditional("router", state2) == "path_b"

    def test_missing_conditional_edge(self):
        executor = GraphExecutor()
        with pytest.raises(NodeExecutionError):
            executor.evaluate_conditional("missing", GraphState())

    def test_node_execution_trace(self):
        executor = GraphExecutor()

        def dummy(state: GraphState) -> GraphState:
            state.final_response = "ok"
            return state

        executor.register_node("trace_test", dummy)
        state = GraphState(query="q")
        result = executor.execute_node("trace_test", state, "trace_phase")
        assert len(result.execution_trace) == 1
        trace = result.execution_trace[0]
        assert trace.node_name == "trace_test"
        assert trace.status == "completed"
        assert trace.duration_ms > 0

    def test_node_error_recorded(self):
        executor = GraphExecutor()

        def failing(state: GraphState) -> GraphState:
            raise ValueError("something went wrong")

        executor.register_node("fail_node", failing)
        with pytest.raises(NodeExecutionError):
            executor.execute_node("fail_node", GraphState(), "fail")
