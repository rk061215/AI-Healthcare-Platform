from __future__ import annotations

from typing import Any, Optional

from app.langgraph.edges import need_retrieval_edge, need_tool_edge
from app.langgraph.graph_runtime import BaseGraph
from app.langgraph.graph_state import GraphState
from app.langgraph.nodes import (
    context_builder_node,
    load_memory_node,
    medical_qa_node,
    persist_memory_node,
    response_generator_node,
    retriever_node,
    tool_executor_node,
    tool_selector_node,
)

START_NODE = "load_memory"
NODE_NAMES = [
    "load_memory",
    "medical_qa",
    "tool_selector",
    "tool_executor",
    "retriever",
    "context_builder",
    "response_generator",
    "persist_memory",
]
END_NODE = "__end__"

PIPELINE_ORDER: list[str] = [
    "load_memory",
    "medical_qa",
    "tool_selector",
    "response_generator",
    "persist_memory",
]


class MedicalQAGraph(BaseGraph):
    def build(self) -> None:
        self._executor.register_node("load_memory", load_memory_node)
        self._executor.register_node("medical_qa", medical_qa_node)
        self._executor.register_node("tool_selector", tool_selector_node)
        self._executor.register_node("tool_executor", tool_executor_node)
        self._executor.register_node("retriever", retriever_node)
        self._executor.register_node("context_builder", context_builder_node)
        self._executor.register_node("response_generator", response_generator_node)
        self._executor.register_node("persist_memory", persist_memory_node)

        self._executor.register_conditional_edge(
            "need_tool", need_tool_edge
        )
        self._executor.register_conditional_edge(
            "need_retrieval", need_retrieval_edge
        )

    def _run_pipeline(self, state: GraphState) -> GraphState:
        if not self._built:
            self.build()
            self._built = True

        state = self._executor.execute_node(
            "load_memory", state, "memory_load"
        )
        if self._should_stop(state):
            return state

        state = self._executor.execute_node(
            "medical_qa", state, "qa_generation"
        )
        if self._should_stop(state):
            return state

        state = self._executor.execute_node(
            "tool_selector", state, "tool_selection"
        )
        if self._should_stop(state):
            return state

        tool_route = self._executor.evaluate_conditional("need_tool", state)
        if tool_route == "tool_executor":
            state = self._executor.execute_node(
                "tool_executor", state, "tool_execution"
            )
            if self._should_stop(state):
                return state

        retrieval_route = self._executor.evaluate_conditional("need_retrieval", state)
        if retrieval_route == "retriever":
            state = self._executor.execute_node(
                "retriever", state, "retrieval"
            )
            if self._should_stop(state):
                return state

            state = self._executor.execute_node(
                "context_builder", state, "context_building"
            )
            if self._should_stop(state):
                return state

        state = self._executor.execute_node(
            "response_generator", state, "response_generation"
        )
        if self._should_stop(state):
            return state

        state = self._executor.execute_node(
            "persist_memory", state, "memory_persist"
        )

        return state

    def _should_stop(self, state: GraphState) -> bool:
        if state.status == "failed":
            return True
        if len(state.errors) > 0 and state.current_node not in (
            "tool_executor",
            "retriever",
            "context_builder",
        ):
            return True
        return False


def create_medical_qa_graph(
    state: Optional[GraphState] = None,
    **kwargs: Any,
) -> MedicalQAGraph:
    from app.langgraph.graph_context import GraphContext
    from app.langgraph.config import LangGraphConfig

    config = LangGraphConfig(graph_name="medical_qa", **kwargs)
    graph_state = state or GraphState(graph_name="medical_qa")
    context = GraphContext(config=config, state=graph_state)
    return MedicalQAGraph(config=config, state=graph_state, context=context)
