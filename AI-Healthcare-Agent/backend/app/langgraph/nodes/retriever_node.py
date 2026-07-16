from __future__ import annotations

from typing import Any, Optional

from app.langgraph.exceptions import NodeExecutionError
from app.langgraph.graph_state import GraphState, GraphPhase
from app.rag.models import RAGRequest


def retriever_node(state: GraphState) -> GraphState:
    state.current_node = "retriever"
    state.phase = GraphPhase.RETRIEVAL.value

    try:
        rag_engine = state.services.get("rag_engine")
        if rag_engine is None:
            state.retrieved_evidence = []
            state.context_updates.append("retriever: no rag_engine available, skipping")
            return state

        request = RAGRequest(
            query=state.query or "",
            patient_id=state.patient_id,
            report_id=state.report_id,
            document_type=state.document_type,
            top_k=10,
            enable_guardrails=True,
            enable_citations=True,
        )

        response = rag_engine.answer(request)

        state.rag_response = {
            "answer": response.answer,
            "query_type": response.query_type,
            "processing_time_ms": response.processing_time_ms,
            "model": response.model,
            "provider": response.provider,
        }

        citations_data = []
        if response.citations:
            for c in response.citations.citations if hasattr(response.citations, "citations") else []:
                citations_data.append({
                    "document_id": getattr(c, "document_id", ""),
                    "chunk_id": getattr(c, "chunk_id", ""),
                    "text": getattr(c, "text", ""),
                    "score": getattr(c, "score", 0.0),
                    "section": getattr(c, "section", None),
                })
        state.retrieved_evidence = citations_data

        state.context_updates.append(
            f"retriever: retrieved {len(citations_data)} evidence items"
        )

    except Exception as exc:
        state.errors.append(f"[retriever] {exc}")
        state.retrieved_evidence = []

    return state
