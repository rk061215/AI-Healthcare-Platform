from __future__ import annotations

import re
from typing import Optional

from app.query_processing.exceptions import DecompositionError
from app.query_processing.models import DecomposedQuestion, UnderstandingIntent


COMPOUND_QUESTION_PATTERNS = [
    re.compile(r"(?i)\b(and|or|also|additionally|moreover|furthermore)\b"),
    re.compile(r"(?i)([?.!]\s*(?:what|who|when|where|why|how|is|are|was|were|do|does|did|can|could|will|would|should|has|have|had))"),
    re.compile(r"(?i)([,;]\s*(?:what|who|when|where|why|how))"),
]

SIMPLE_QUESTION_PATTERNS = [
    re.compile(r"(?i)^(what|who|when|where|why|how|is|are|was|were|do|does|did|can|could|will|would|should|has|have|had)"),
    re.compile(r"(?i)[?.!]\s*$"),
]


class QuestionDecomposer:
    def __init__(self, max_sub_questions: int = 5):
        self._max = max_sub_questions

    def decompose(self, query: str) -> list[DecomposedQuestion]:
        if not query or not query.strip():
            return []

        try:
            cleaned = query.strip()

            is_compound = self._is_compound(cleaned)
            if not is_compound:
                return [
                    DecomposedQuestion(
                        text=cleaned,
                        intent=self._infer_intent(cleaned),
                        requires_retrieval=True,
                        weight=1.0,
                    )
                ]

            parts = self._split_questions(cleaned)
            if len(parts) <= 1:
                return [
                    DecomposedQuestion(
                        text=cleaned,
                        intent=self._infer_intent(cleaned),
                        requires_retrieval=True,
                        weight=1.0,
                    )
                ]

            result: list[DecomposedQuestion] = []
            for i, part in enumerate(parts[:self._max]):
                part = part.strip()
                if not part or len(part) < 3:
                    continue
                result.append(DecomposedQuestion(
                    text=part,
                    intent=self._infer_intent(part),
                    target_entities=[],
                    requires_retrieval=True,
                    weight=round(1.0 / len(parts), 2) if len(parts) > 1 else 1.0,
                ))

            return result
        except Exception as exc:
            raise DecompositionError(f"Question decomposition failed: {exc}") from exc

    def _is_compound(self, query: str) -> bool:
        query_lower = query.lower()
        qmark_count = query_lower.count("?")
        if qmark_count > 1:
            return True
        if qmark_count == 0:
            for sep in [" and ", " or ", " also ", " additionally "]:
                if sep in query_lower:
                    for qpat in SIMPLE_QUESTION_PATTERNS:
                        if qpat.search(query_lower):
                            return True
        return False

    def _split_questions(self, query: str) -> list[str]:
        parts = re.split(r'[?.!]\s*(?=[A-Za-z])', query)
        if len(parts) > 1:
            return [p.strip() for p in parts if p.strip()]

        for sep in [" and ", " or ", " also ", " additionally "]:
            if sep in query.lower():
                sub = re.split(rf'(?i)\s*{sep.strip()}\s*', query, maxsplit=1)
                if len(sub) > 1 and all(
                    any(qp.search(s) for qp in SIMPLE_QUESTION_PATTERNS)
                    for s in sub
                ):
                    return sub
        return [query]

    def _infer_intent(self, question: str) -> UnderstandingIntent:
        q = question.lower().strip()

        if re.search(r"\b(what is|what are|define|describe|explain|tell me about)\b", q):
            return UnderstandingIntent.informational
        if re.search(r"\b(how (do|to|can|should|would)|steps? to|procedure|guide)\b", q):
            return UnderstandingIntent.instructional
        if re.search(r"\b(difference|compare|contrast|vs|versus|better|worse|alternative)\b", q):
            return UnderstandingIntent.comparative
        if re.search(r"\b(do i have|am i|diagnos|what (condition|disease|disorder))\b", q):
            return UnderstandingIntent.diagnostic
        if re.search(r"\b(will I|outlook|prognosis|survival|recover|chance|likely)\b", q):
            return UnderstandingIntent.prognostic
        if re.search(r"\b(appointment|schedule|book|reschedule|when.*(see|visit|follow))\b", q):
            return UnderstandingIntent.administrative
        if re.search(r"\b(why|how (come|is it)|what causes|reason|cause)\b", q):
            return UnderstandingIntent.exploratory
        if re.search(r"\b(fix|treat|help|remedy|stop|prevent|avoid|what should (i|I)|any (solution|remedy))\b", q):
            return UnderstandingIntent.troubleshooting
        if re.search(r"\b(what|who|when|where|how)\b", q):
            return UnderstandingIntent.factual

        return UnderstandingIntent.factual
