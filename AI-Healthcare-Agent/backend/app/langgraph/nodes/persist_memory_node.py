from __future__ import annotations

from typing import Any

from app.langgraph.graph_state import GraphState, GraphPhase


def persist_memory_node(state: GraphState) -> GraphState:
    state.current_node = "persist_memory"
    state.phase = GraphPhase.MEMORY_PERSIST.value

    try:
        memory_service = state.services.get("memory_service")
        if memory_service is None:
            state.context_updates.append("persist_memory: no memory_service available, skipping")
            return state

        session_id = state.session_id
        if not session_id:
            state.context_updates.append("persist_memory: no session_id, skipping")
            return state

        query = state.query or ""
        answer = state.final_response or ""
        if not query and not answer:
            state.context_updates.append("persist_memory: no query or answer to persist")
            return state

        entry = memory_service.extract_from_chat(
            session_id=session_id,
            query=query,
            answer=answer,
            query_type=state.rag_response.get("query_type", "unknown") if state.rag_response else "unknown",
            confidence=0.8,
        )

        state.persisted_memory_id = entry.memory_id if hasattr(entry, "memory_id") else str(entry)
        state.context_updates.append(
            f"persist_memory: persisted memory entry {state.persisted_memory_id}"
        )

    except Exception as exc:
        state.errors.append(f"[persist_memory] {exc}")
        state.persisted_memory_id = ""

    return state
