from __future__ import annotations

from typing import Any

from app.langgraph.graph_state import GraphState, GraphPhase


TOOL_TRIGGER_KEYWORDS: list[str] = [
    "schedule", "appointment", "book", "reschedule", "cancel",
    "remind", "notify", "send", "email", "message",
    "update", "change", "modify", "create", "delete",
    "search patient", "find patient", "lookup",
]


def tool_selector_node(state: GraphState) -> GraphState:
    state.current_node = "tool_selector"
    state.phase = GraphPhase.TOOL_SELECTION.value

    try:
        query_lower = (state.query or "").lower()
        matched_keywords = [
            kw for kw in TOOL_TRIGGER_KEYWORDS
            if kw in query_lower
        ]

        if matched_keywords:
            state.tool_decision = {
                "needs_tool": True,
                "matched_keywords": matched_keywords,
                "reasoning": f"Query matched tool keywords: {matched_keywords}",
            }
            state.context_updates.append(
                f"tool_selector: tool needed based on keywords: {matched_keywords}"
            )
        else:
            state.tool_decision = {
                "needs_tool": False,
                "matched_keywords": [],
                "reasoning": "No tool-related keywords detected in query",
            }
            state.context_updates.append("tool_selector: no tool needed")

        state.need_tool = state.tool_decision["needs_tool"]

    except Exception as exc:
        state.errors.append(f"[tool_selector] {exc}")
        state.tool_decision = {"needs_tool": False, "matched_keywords": [], "reasoning": f"Error: {exc}"}
        state.need_tool = False

    return state
