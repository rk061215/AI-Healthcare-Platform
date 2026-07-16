from __future__ import annotations

from typing import Any, Optional

from app.chat.models import ConfidenceLevel, ConfidenceScore

SUFFICIENT_CONTEXT_PHRASES: list[str] = [
    "i don't have enough", "no information", "context does not",
    "not mentioned", "not provided", "cannot find", "not available",
    "insufficient", "unable to answer", "no data",
]


class ConfidenceCalculator:
    """Calculates confidence scores based on retrieval evidence.

    Confidence is derived from:
    - Average retrieval score across supporting chunks
    - Number of supporting chunks
    - Citation coverage ratio
    - Guardrail validation pass/fail
    - Unknown answer detection via insufficient context phrases

    Does NOT use LLM confidence. Relies entirely on retrieval metrics.
    """

    def __init__(
        self,
        min_chunks: int = 2,
        min_score: float = 0.5,
        citation_coverage_min: float = 0.3,
    ) -> None:
        self._min_chunks = min_chunks
        self._min_score = min_score
        self._citation_coverage_min = citation_coverage_min

    def calculate(
        self,
        retrieval_scores: list[float],
        num_chunks: int = 0,
        num_citations: int = 0,
        guardrail_passed: bool = True,
        guardrail_failures: Optional[list[str]] = None,
        answer_text: str = "",
        has_sufficient_context: bool = True,
    ) -> ConfidenceScore:
        avg_score = self._avg(retrieval_scores) if retrieval_scores else 0.0
        chunk_count = max(num_chunks, len(retrieval_scores))
        citation_coverage = self._calc_citation_coverage(
            chunk_count, num_citations
        )

        insufficient_evidence = self._detect_insufficient_evidence(
            answer_text=answer_text,
            has_sufficient_context=has_sufficient_context,
            guardrail_failures=guardrail_failures or [],
            chunk_count=chunk_count,
        )

        retrieval_factor = min(avg_score / max(self._min_score, 0.01), 1.0)
        chunk_factor = min(chunk_count / max(self._min_chunks, 1), 1.0)
        citation_factor = min(
            citation_coverage / max(self._citation_coverage_min, 0.01), 1.0
        )
        guardrail_factor = 1.0 if guardrail_passed else 0.5

        if insufficient_evidence:
            overall = min(
                retrieval_factor * 0.4 + chunk_factor * 0.3
                + citation_factor * 0.2 + guardrail_factor * 0.1,
                0.3,
            )
        else:
            overall = (
                retrieval_factor * 0.35
                + chunk_factor * 0.25
                + citation_factor * 0.25
                + guardrail_factor * 0.15
            )

        overall = round(min(max(overall, 0.0), 1.0), 4)

        return ConfidenceScore(
            overall=overall,
            level=self._classify_level(overall, insufficient_evidence),
            retrieval_score=round(avg_score, 4),
            chunk_count=chunk_count,
            citation_coverage=round(citation_coverage, 4),
            guardrail_validated=guardrail_passed,
            insufficient_evidence=insufficient_evidence,
        )

    def _avg(self, scores: list[float]) -> float:
        return sum(scores) / len(scores) if scores else 0.0

    def _calc_citation_coverage(
        self, chunk_count: int, num_citations: int
    ) -> float:
        if chunk_count == 0:
            return 0.0
        return min(num_citations / chunk_count, 1.0)

    def _detect_insufficient_evidence(
        self,
        answer_text: str,
        has_sufficient_context: bool,
        guardrail_failures: list[str],
        chunk_count: int,
    ) -> bool:
        if not has_sufficient_context:
            return True
        if chunk_count == 0:
            return True
        if guardrail_failures:
            return True
        answer_lower = answer_text.lower()
        if any(phrase in answer_lower for phrase in SUFFICIENT_CONTEXT_PHRASES):
            return True
        return False

    def _classify_level(
        self, overall: float, insufficient_evidence: bool
    ) -> ConfidenceLevel:
        if insufficient_evidence:
            return ConfidenceLevel.insufficient_evidence
        if overall >= 0.7:
            return ConfidenceLevel.high
        if overall >= 0.4:
            return ConfidenceLevel.medium
        return ConfidenceLevel.low
