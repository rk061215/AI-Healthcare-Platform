from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.rag.models import RewrittenQuery


class BaseQueryRewriter(ABC):
    """Abstract interface for query rewriting/expansion.

    Implementations can be:
    - Rule-based: synonym expansion, abbreviation expansion
    - LLM-based: generate alternative phrasings, decompose complex questions
    - Hybrid: rule-based pre-processing + LLM refinement
    """

    @abstractmethod
    def rewrite(self, query: str, context: Optional[str] = None) -> RewrittenQuery:
        """Rewrite or expand the query to improve retrieval quality.

        Args:
            query: The original user query.
            context: Optional retrieval context or conversation history.

        Returns:
            RewrittenQuery with the rewritten text and any expansions.
        """


class DefaultQueryRewriter(BaseQueryRewriter):
    """Lightweight rule-based query rewriter.

    Expands common medical abbreviations and adds synonyms.
    Suitable for MVP before an LLM-based rewriter is implemented.
    """

    ABBREVIATIONS: dict[str, str] = {
        "rx": "prescription",
        "tx": "treatment",
        "dx": "diagnosis",
        "hx": "history",
        "sx": "symptoms",
        "fx": "fracture",
        "bid": "twice daily",
        "tid": "three times daily",
        "qid": "four times daily",
        "prn": "as needed",
        "po": "by mouth",
        "od": "right eye",
        "os": "left eye",
        "ou": "both eyes",
        "im": "intramuscular",
        "iv": "intravenous",
        "sc": "subcutaneous",
        "sl": "sublingual",
        "pr": "per rectum",
    }

    MEDICAL_SYNONYMS: dict[str, list[str]] = {
        "medication": ["medicine", "drug", "prescription", "pharmaceutical"],
        "diagnosis": ["condition", "disease", "disorder", "illness"],
        "lab": ["test", "laboratory", "blood work", "analysis"],
        "doctor": ["physician", "provider", "specialist", "clinician"],
        "appointment": ["visit", "consultation", "checkup", "follow-up"],
        "pain": ["discomfort", "ache", "soreness", "tenderness"],
        "surgery": ["operation", "procedure", "surgical intervention"],
    }

    def __init__(self, expand_abbreviations: bool = True, add_synonyms: bool = True) -> None:
        self._expand_abbr = expand_abbreviations
        self._add_syn = add_synonyms

    def rewrite(self, query: str, context: Optional[str] = None) -> RewrittenQuery:
        if not query or not query.strip():
            return RewrittenQuery(original=query or "", rewritten=query or "", strategy="none")

        original = query.strip()
        rewritten = original
        expansions: list[str] = []

        if self._expand_abbr:
            rewritten, abbr_expansions = self._expand_abbreviations(rewritten)
            expansions.extend(abbr_expansions)

        if self._add_syn:
            rewritten, syn_expansions = self._add_synonym_variants(rewritten)
            expansions.extend(syn_expansions)

        strategy = "none"
        if expansions:
            strategy = "expansion"
            if rewritten != original:
                strategy = "rewrite_and_expand"
        elif rewritten != original:
            strategy = "rewrite_only"

        return RewrittenQuery(
            original=original,
            rewritten=rewritten,
            expansions=expansions,
            strategy=strategy,
        )

    def _expand_abbreviations(self, text: str) -> tuple[str, list[str]]:
        words = text.split()
        expanded: list[str] = []
        found: list[str] = []

        for word in words:
            word_lower = word.lower().strip(".,;:!?")
            if word_lower in self.ABBREVIATIONS:
                expansion = self.ABBREVIATIONS[word_lower]
                expanded.append(expansion)
                found.append(f"{word_lower} -> {expansion}")
            else:
                expanded.append(word)

        return " ".join(expanded), found

    def _add_synonym_variants(self, text: str) -> tuple[str, list[str]]:
        found: list[str] = []
        text_lower = text.lower()

        for term, synonyms in self.MEDICAL_SYNONYMS.items():
            if term in text_lower:
                existing = {term}
                relevant = [s for s in synonyms if s not in existing]
                if relevant:
                    found.append(f"{term} -> {', '.join(relevant)}")

        return text, found
