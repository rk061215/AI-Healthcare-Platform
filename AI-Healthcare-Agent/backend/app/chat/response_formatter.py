from __future__ import annotations

from typing import Any, Optional

from app.chat.models import (
    CHAT_SCHEMA_VERSION,
    ConfidenceLevel,
    ConfidenceScore,
    SuggestedQuestion,
)
from app.rag.models import CitationEntry


class ResponseFormatter:
    """Formats RAG responses into structured chat answers.

    Handles:
    - Answer formatting with optional structure
    - Citation formatting
    - Confidence display
    - Unknown-answer detection and messaging
    """

    UNKNOWN_ANSWER_TEMPLATE = (
        "I don't have enough information to answer that question based "
        "on the medical documents available. Please try rephrasing your "
        "question, or ask about something else from your medical report."
    )

    LOW_CONFIDENCE_PREFIX = (
        "Based on the available information, here is what I found:"
    )

    def format_answer(
        self,
        answer: str,
        confidence: ConfidenceScore,
        citations: Optional[list[Any]] = None,
        suggested_questions: Optional[list[SuggestedQuestion]] = None,
        query_type: str = "unknown",
        is_follow_up: bool = False,
    ) -> dict[str, Any]:
        if self._is_unknown_answer(answer, confidence):
            formatted = self.UNKNOWN_ANSWER_TEMPLATE
        elif confidence.level in (
            ConfidenceLevel.low, ConfidenceLevel.insufficient_evidence
        ):
            formatted = f"{self.LOW_CONFIDENCE_PREFIX}\n\n{answer}"
        else:
            formatted = answer

        formatted_citations = self._format_citations(
            citations or [], formatted
        )

        return {
            "answer": formatted,
            "citations": formatted_citations,
            "confidence": confidence,
            "suggested_questions": suggested_questions or [],
            "query_type": query_type,
            "is_follow_up": is_follow_up,
            "schema_version": CHAT_SCHEMA_VERSION,
        }

    def format_report_summary(
        self,
        answer: str,
        sections: list[str],
        confidence: ConfidenceScore,
    ) -> str:
        parts: list[str] = []

        parts.append("## Medical Report Summary\n")
        parts.append(answer)

        if sections:
            parts.append("\n### Sections Found in Report")
            for s in sections:
                parts.append(f"- {s}")

        if confidence.level == ConfidenceLevel.insufficient_evidence:
            parts.append(
                "\n*Note: The summary may be incomplete due to "
                "limited information in the available documents.*"
            )

        return "\n".join(parts)

    def _is_unknown_answer(
        self, answer: str, confidence: ConfidenceScore
    ) -> bool:
        if confidence.insufficient_evidence:
            return True
        if confidence.level == ConfidenceLevel.insufficient_evidence:
            return True
        answer_lower = answer.lower().strip()
        insufficient_phrases = [
            "i don't have enough", "no information", "context does not",
            "not mentioned", "not provided", "cannot find", "not available",
            "insufficient", "unable to answer", "no data",
        ]
        if any(phrase in answer_lower for phrase in insufficient_phrases):
            return True
        return False

    def _format_citations(
        self,
        citations: list[Any],
        answer: str,
    ) -> list[dict[str, Any]]:
        if not citations:
            return []
        result: list[dict[str, Any]] = []
        seen: set[str] = set()
        for c in citations:
            chunk_id = self._get_attr(c, "chunk_id", "")
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            result.append({
                "id": self._get_attr(c, "citation_id", 0),
                "document_id": self._get_attr(c, "document_id", ""),
                "section": self._get_attr(c, "section", ""),
                "source": self._get_attr(c, "source", ""),
                "text_snippet": self._get_attr(c, "text_snippet", ""),
            })
        return result

    def _get_attr(self, obj: Any, attr: str, default: Any = "") -> Any:
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)
