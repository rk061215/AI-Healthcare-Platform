from __future__ import annotations

from typing import Any

from app.agents.agent_context import AgentContext
from app.langgraph.exceptions import NodeExecutionError
from app.langgraph.graph_state import GraphState, GraphPhase


def medical_qa_node(state: GraphState) -> GraphState:
    state.current_node = "medical_qa"
    state.phase = GraphPhase.QA_GENERATION.value

    try:
        agent_executor = state.services.get("agent_executor")
        if agent_executor is None:
            raise NodeExecutionError("agent_executor not available in state.services")

        context = AgentContext(
            query=state.query,
            session_id=state.session_id,
            patient_id=state.patient_id or "",
            document_id=state.document_id,
            report_id=state.report_id,
            document_type=state.document_type,
            document_sections=state.document_sections,
            memory_entries=state.memory_entries,
            language=state.language,
        )

        response = agent_executor.execute(context)
        state.agent_response = {
            "success": response.success,
            "answer": response.answer,
            "error": response.error,
            "total_duration_ms": response.total_duration_ms,
            "token_usage": dict(response.token_usage) if response.token_usage else {},
            "citations": [dict(c) for c in (response.citations or [])],
        }
        state.final_response = response.answer if response.success else ""
        state.token_usage = dict(response.token_usage) if response.token_usage else {}

        if response.success:
            state.context_updates.append(
                f"medical_qa: agent executed successfully, answer length={len(response.answer)}"
            )
        else:
            state.errors.append(f"[medical_qa] agent execution failed: {response.error}")

    except Exception as exc:
        state.errors.append(f"[medical_qa] {exc}")
        state.agent_response = {"success": False, "error": str(exc)}

    return state
