from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.rag.citation_manager import CitationManager
from app.rag.exceptions import CitationError
from app.rag.models import CitationBlock, CitationEntry, RAGContext


class CitationScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    citation_id: int
    relevance_score: float = 0.0
    source_quality: float = 0.5
    recency_weight: float = 1.0
    overall: float = 0.0


class CitationGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    group_key: str
    citations: list[CitationEntry] = Field(default_factory=list)
    total_score: float = 0.0


class CitationAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total_citations: int = 0
    scored_citations: list[CitationScore] = Field(default_factory=list)
    groups: list[CitationGroup] = Field(default_factory=list)
    coverage_score: float = 0.0
    has_contradictions: bool = False
    average_relevance: float = 0.0


class CitationEngine:
    def __init__(
        self,
        citation_manager: Optional[CitationManager] = None,
        include_scores: bool = True,
    ):
        self._base = citation_manager or CitationManager(include_scores=include_scores)
        self._include_scores = include_scores

    def extract_citations(self, context: RAGContext) -> CitationBlock:
        return self._base.extract_citations(context)

    def format_inline_citation(self, citation_id: int) -> str:
        return self._base.format_inline_citation(citation_id)

    def has_hallucinated_citations(
        self, response: str, citations: CitationBlock
    ) -> list[dict[str, Any]]:
        return self._base.has_hallucinated_citations(response, citations)

    def validate_response_grounding(
        self, response: str, citations: CitationBlock
    ) -> dict[str, Any]:
        return self._base.validate_response_grounding(response, citations)

    def analyze_citations(self, citations: CitationBlock) -> CitationAnalysis:
        if not citations.citations:
            return CitationAnalysis()

        scored = []
        for entry in citations.citations:
            relevance = min(entry.score * 1.5, 1.0) if entry.score > 0 else 0.5
            quality = self._score_source_quality(entry)
            overall = (relevance * 0.5 + quality * 0.3 + 0.2)
            scored.append(CitationScore(
                citation_id=entry.citation_id,
                relevance_score=round(relevance, 4),
                source_quality=round(quality, 4),
                overall=round(overall, 4),
            ))

        groups = self._group_citations(citations.citations)

        avg_relevance = (
            sum(s.overall for s in scored) / len(scored)
            if scored else 0.0
        )

        coverage = min(len(citations.citations) / 3.0, 1.0)
        contradictions = self._check_contradictions(citations.citations)

        return CitationAnalysis(
            total_citations=len(citations.citations),
            scored_citations=scored,
            groups=groups,
            coverage_score=round(coverage, 4),
            has_contradictions=contradictions,
            average_relevance=round(avg_relevance, 4),
        )

    def extract_inline_citations(self, response: str) -> list[dict[str, Any]]:
        refs: list[dict[str, Any]] = []
        for match in re.finditer(r"\[citation:(\d+)\]", response):
            refs.append({
                "citation_id": int(match.group(1)),
                "position": match.start(),
                "text": match.group(0),
            })
        return refs

    def get_claim_citation_map(
        self, response: str, citations: CitationBlock
    ) -> dict[str, list[int]]:
        sentences = re.split(r'(?<=[.!?])\s+', response)
        claim_map: dict[str, list[int]] = {}

        for sentence in sentences:
            refs = re.findall(r"\[citation:(\d+)\]", sentence)
            if refs:
                clean = re.sub(r"\s*\[citation:\d+\]\s*", "", sentence).strip()
                if clean:
                    claim_map[clean] = [int(r) for r in refs]

        return claim_map

    def _score_source_quality(self, entry: CitationEntry) -> float:
        quality = 0.5
        if entry.source == "ocr":
            quality = 0.4
        elif entry.source in ("lab_result", "medication"):
            quality = 0.8
        elif entry.source == "doctor_notes":
            quality = 0.7
        if entry.section:
            quality += 0.1
        if entry.page is not None:
            quality += 0.1
        return min(quality, 1.0)

    def _group_citations(self, entries: list[CitationEntry]) -> list[CitationGroup]:
        groups: dict[str, list[CitationEntry]] = defaultdict(list)
        for entry in entries:
            key = entry.source or "unknown"
            groups[key].append(entry)

        result = []
        for key, members in groups.items():
            total_score = sum(e.score for e in members)
            result.append(CitationGroup(
                group_key=key,
                citations=members,
                total_score=round(total_score, 4),
            ))

        result.sort(key=lambda g: g.total_score, reverse=True)
        return result

    def _check_contradictions(self, entries: list[CitationEntry]) -> bool:
        text_signals: dict[str, list[str]] = defaultdict(list)
        for entry in entries:
            for word in entry.text_snippet.lower().split():
                if word in ("positive", "negative", "normal", "abnormal",
                            "elevated", "decreased", "increased", "present",
                            "absent", "improved", "worsened"):
                    text_signals[word].append(entry.chunk_id)

        opposites = [
            ("positive", "negative"),
            ("normal", "abnormal"),
            ("elevated", "decreased"),
            ("increased", "decreased"),
            ("present", "absent"),
            ("improved", "worsened"),
        ]

        for a, b in opposites:
            if a in text_signals and b in text_signals:
                return True

        return False
