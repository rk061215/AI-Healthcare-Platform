from __future__ import annotations

from typing import Any

from app.langgraph.graph_state import GraphState, GraphPhase


def response_generator_node(state: GraphState) -> GraphState:
    state.current_node = "response_generator"
    state.phase = GraphPhase.RESPONSE_GENERATION.value

    try:
        agent_response = state.agent_response or {}
        rag_response = state.rag_response or {}
        tool_result = state.tool_result or {}

        if agent_response.get("success") and agent_response.get("answer"):
            final = agent_response["answer"]
            source = "agent"
        elif rag_response.get("answer"):
            final = rag_response["answer"]
            source = "rag"
        elif tool_result.get("success") and tool_result.get("data"):
            data = tool_result["data"]
            final = str(data) if not isinstance(data, str) else data
            source = "tool"
        else:
            final = "I'm unable to process your request at this time. Please try rephrasing your question."
            source = "fallback"

        state.final_response = final
        state.response_metadata = {
            "source": source,
            "has_agent_answer": agent_response.get("success", False),
            "has_rag_answer": bool(rag_response.get("answer")),
            "has_tool_result": tool_result.get("success", False),
            "answer_length": len(final),
        }

        state.context_updates.append(
            f"response_generator: generated response from {source} source"
        )

    except Exception as exc:
        state.errors.append(f"[response_generator] {exc}")
        state.final_response = state.final_response or "An error occurred while generating the response."

    return state
