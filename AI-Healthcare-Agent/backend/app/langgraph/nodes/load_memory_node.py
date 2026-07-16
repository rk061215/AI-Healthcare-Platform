from __future__ import annotations

from typing import Any

from app.langgraph.graph_state import GraphState, GraphPhase


def load_memory_node(state: GraphState) -> GraphState:
    state.current_node = "load_memory"
    state.phase = GraphPhase.MEMORY_LOAD.value

    try:
        memory_service = state.services.get("memory_service")
        if memory_service is None:
            state.memory_entries = []
            state.context_updates.append("load_memory: no memory_service available, skipping")
            return state

        session_id = state.session_id
        if not session_id:
            state.memory_entries = []
            return state

        entries = memory_service.recall(session_id=session_id, limit=20)
        state.memory_entries = [
            {
                "memory_id": e.memory_id,
                "memory_type": e.memory_type.value if hasattr(e.memory_type, "value") else str(e.memory_type),
                "content": e.content,
                "importance": e.importance,
                "created_at": e.created_at.isoformat() if hasattr(e.created_at, "isoformat") else str(e.created_at),
            }
            for e in entries
        ] if entries else []

        state.context_updates.append(
            f"load_memory: loaded {len(state.memory_entries)} memory entries"
        )

    except Exception as exc:
        state.errors.append(f"[load_memory] {exc}")
        state.memory_entries = []

    return state
