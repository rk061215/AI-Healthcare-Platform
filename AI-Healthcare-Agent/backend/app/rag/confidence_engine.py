from __future__ import annotations

import re
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.rag.citation_engine import CitationAnalysis, CitationEngine
from app.rag.models import CitationBlock


class ClaimConfidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    claim_text: str
    confidence: float = 0.0
    supporting_citations: list[int] = Field(default_factory=list)
    has_citation: bool = False
    is_subjective: bool = False


class ConfidenceBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")
    citation_coverage: float = 0.0
    source_quality: float = 0.0
    claim_support: float = 0.0
    hallucination_risk: float = 0.0
    completeness: float = 0.0


class ConfidenceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    overall_confidence: float = 0.0
    breakdown: ConfidenceBreakdown = Field(default_factory=ConfidenceBreakdown)
    claim_confidences: list[ClaimConfidence] = Field(default_factory=list)
    requires_human_review: bool = False
    warnings: list[str] = Field(default_factory=list)


CONFIDENCE_THRESHOLDS = {
    "high": 0.8,
    "medium": 0.5,
    "low": 0.0,
}


class ConfidenceEngine:
    def __init__(
        self,
        citation_engine: Optional[CitationEngine] = None,
        high_threshold: float = 0.8,
        medium_threshold: float = 0.5,
    ):
        self._citation_engine = citation_engine or CitationEngine()
        self._high = high_threshold
        self._medium = medium_threshold

    def evaluate(
        self,
        response: str,
        citations: CitationBlock,
        citation_analysis: Optional[CitationAnalysis] = None,
    ) -> ConfidenceResult:
        if not response:
            return ConfidenceResult(
                overall_confidence=0.0,
                requires_human_review=True,
                warnings=["Empty response"],
            )

        if citation_analysis is None:
            citation_analysis = self._citation_engine.analyze_citations(citations)

        breakdown = self._compute_breakdown(response, citations, citation_analysis)
        claim_confidences = self._analyze_claims(response, citations)
        overall = self._compute_overall(breakdown, claim_confidences)

        warnings = []
        if overall < self._medium:
            warnings.append("Low overall confidence — response may be unreliable")
        if breakdown.hallucination_risk > 0.5:
            warnings.append("Elevated hallucination risk detected")
        if breakdown.completeness < 0.3:
            warnings.append("Response may be incomplete")

        requires_review = (
            overall < self._medium
            or breakdown.hallucination_risk > 0.7
        )

        return ConfidenceResult(
            overall_confidence=round(overall, 4),
            breakdown=breakdown,
            claim_confidences=claim_confidences,
            requires_human_review=requires_review,
            warnings=warnings,
        )

    def get_confidence_label(self, confidence: float) -> str:
        if confidence >= self._high:
            return "high"
        if confidence >= self._medium:
            return "medium"
        return "low"

    def _compute_breakdown(
        self,
        response: str,
        citations: CitationBlock,
        analysis: CitationAnalysis,
    ) -> ConfidenceBreakdown:
        if not citations.citations:
            return ConfidenceBreakdown()

        citation_coverage = analysis.coverage_score

        if analysis.scored_citations:
            source_quality = sum(
                s.source_quality for s in analysis.scored_citations
            ) / len(analysis.scored_citations)
        else:
            source_quality = 0.0

        inline_refs = self._citation_engine.extract_inline_citations(response)
        total_sentences = max(len(re.split(r'(?<=[.!?])\s+', response)), 1)
        claim_support = len(inline_refs) / max(total_sentences * 0.5, 1)
        claim_support = min(claim_support, 1.0)

        hallucinated = self._citation_engine.has_hallucinated_citations(
            response, citations
        )
        hallucination_risk = min(len(hallucinated) / max(len(inline_refs), 1), 1.0)

        total_possible_citations = max(len(citations.citations), 1)
        completeness = len(set(
            r["citation_id"] for r in inline_refs
        )) / total_possible_citations

        return ConfidenceBreakdown(
            citation_coverage=round(citation_coverage, 4),
            source_quality=round(source_quality, 4),
            claim_support=round(claim_support, 4),
            hallucination_risk=round(hallucination_risk, 4),
            completeness=round(completeness, 4),
        )

    def _analyze_claims(
        self,
        response: str,
        citations: CitationBlock,
    ) -> list[ClaimConfidence]:
        sentences = re.split(r'(?<=[.!?])\s+', response)
        claim_confidences: list[ClaimConfidence] = []

        for sentence in sentences:
            clean = sentence.strip()
            if not clean:
                continue

            refs = re.findall(r"\[citation:(\d+)\]", clean)
            has_citation = len(refs) > 0
            clean_text = re.sub(r"\s*\[citation:\d+\]\s*", "", clean).strip()

            is_subjective = self._is_subjective_claim(clean_text)

            if has_citation and refs:
                valid_ids = {str(c.citation_id) for c in citations.citations}
                valid_refs = [int(r) for r in refs if r in valid_ids]
                confidence = min(len(valid_refs) * 0.3 + 0.4, 1.0)
            elif not has_citation:
                confidence = 0.2
            else:
                confidence = 0.1

            if is_subjective:
                confidence *= 0.5

            claim_confidences.append(ClaimConfidence(
                claim_text=clean_text[:200],
                confidence=round(confidence, 4),
                supporting_citations=[int(r) for r in refs if r.isdigit()],
                has_citation=has_citation,
                is_subjective=is_subjective,
            ))

        return claim_confidences

    def _compute_overall(
        self,
        breakdown: ConfidenceBreakdown,
        claim_confidences: list[ClaimConfidence],
    ) -> float:
        if not claim_confidences:
            return 0.0

        avg_claim_conf = sum(c.confidence for c in claim_confidences) / len(claim_confidences)

        overall = (
            breakdown.citation_coverage * 0.20
            + breakdown.source_quality * 0.15
            + breakdown.claim_support * 0.20
            + (1.0 - breakdown.hallucination_risk) * 0.25
            + breakdown.completeness * 0.10
            + avg_claim_conf * 0.10
        )

        return max(0.0, min(overall, 1.0))

    def _is_subjective_claim(self, text: str) -> bool:
        subjective_indicators = [
            r"\b(I think|I believe|I feel|I guess|maybe|perhaps|possibly|likely|probably)\b",
            r"\b(might|could|may)\b",
            r"\b(in my opinion|it seems|appears to be|suggests that)\b",
        ]
        text_lower = text.lower()
        for pattern in subjective_indicators:
            if re.search(pattern, text_lower):
                return True
        return False
