from __future__ import annotations

from app.langgraph.graph_state import GraphState


def need_retrieval_edge(state: GraphState) -> str:
    if state.need_retrieval:
        return "retriever"
    return "response_generator"
