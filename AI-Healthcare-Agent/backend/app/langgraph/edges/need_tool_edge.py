from __future__ import annotations

from app.langgraph.graph_state import GraphState


def need_tool_edge(state: GraphState) -> str:
    if state.need_tool:
        return "tool_executor"
    return "need_retrieval"
