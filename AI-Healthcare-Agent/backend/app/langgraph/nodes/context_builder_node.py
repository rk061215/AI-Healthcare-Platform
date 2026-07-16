from __future__ import annotations

from typing import Any

from app.langgraph.graph_state import GraphState, GraphPhase


def context_builder_node(state: GraphState) -> GraphState:
    state.current_node = "context_builder"
    state.phase = GraphPhase.CONTEXT_BUILDING.value

    try:
        context_builder_svc = state.services.get("context_builder")
        if context_builder_svc is None:
            state.context_updates.append("context_builder: no context_builder service available, skipping")
            return state

        from app.context.models import BuildContextInput, ContextFragment, CitationInfo

        evidence = state.retrieved_evidence
        if not evidence:
            state.context_updates.append("context_builder: no evidence to build context from")
            return state

        fragments = []
        for i, ev in enumerate(evidence):
            citation = CitationInfo(
                document_id=ev.get("document_id", ""),
                chunk_id=ev.get("chunk_id", ""),
                section=ev.get("section"),
            )
            fragment = ContextFragment(
                text=ev.get("text", ""),
                score=ev.get("score", 0.0),
                citation=citation,
                original_chunk_index=i,
                rank=i + 1,
            )
            fragments.append(fragment)

        build_input = BuildContextInput(
            query=state.query or "",
            fragments=fragments,
            max_tokens=4000,
            include_citations=True,
        )

        result = context_builder_svc.build_from_fragments(
            fragments=fragments,
            query=state.query or "",
            max_tokens=4000,
        )

        state.built_context = result.context if hasattr(result, "context") else ""
        state.citations = [
            {
                "document_id": c.document_id,
                "chunk_id": c.chunk_id,
                "section": c.section,
            }
            for c in (result.citations if hasattr(result, "citations") else [])
        ]

        state.context_updates.append(
            f"context_builder: built context with {len(fragments)} fragments, "
            f"context length={len(state.built_context)} chars"
        )

    except Exception as exc:
        state.errors.append(f"[context_builder] {exc}")
        state.built_context = state.built_context or ""

    return state
