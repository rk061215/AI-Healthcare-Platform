from __future__ import annotations

from typing import Any

from app.langgraph.exceptions import NodeExecutionError
from app.langgraph.graph_state import GraphState, GraphPhase


def tool_executor_node(state: GraphState) -> GraphState:
    state.current_node = "tool_executor"
    state.phase = GraphPhase.TOOL_EXECUTION.value

    try:
        tool_service = state.services.get("tool_service")
        if tool_service is None:
            raise NodeExecutionError("tool_service not available in state.services")

        query = state.query or ""
        patient_id = state.patient_id or ""
        session_id = state.session_id

        result = tool_service.run_from_query(
            query=query,
            patient_id=patient_id,
            session_id=session_id,
        )

        state.tool_result = {
            "success": result.success,
            "data": result.data,
            "error": result.error_message,
            "tool_name": result.tool_name,
            "action": result.action,
            "duration_ms": result.duration_ms,
        }

        if result.success:
            state.context_updates.append(
                f"tool_executor: tool '{result.tool_name}' executed successfully"
            )
        else:
            state.errors.append(f"[tool_executor] tool failed: {result.error_message}")

    except Exception as exc:
        state.errors.append(f"[tool_executor] {exc}")
        state.tool_result = {"success": False, "error": str(exc)}

    return state
