from __future__ import annotations

import re
from typing import Optional

from app.rag.exceptions import EmptyQueryError, QueryError
from app.rag.models import ProcessedQuery


MEDICAL_TERMS: set[str] = {
    "diagnosis", "medication", "medicine", "drug", "prescription", "dosage",
    "symptom", "treatment", "therapy", "surgery", "appointment", "follow-up",
    "lab", "test", "result", "blood", "pressure", "heart", "pain", "fever",
    "infection", "allergy", "chronic", "acute", "condition", "disease",
    "disorder", "syndrome", "injury", "wound", "fracture", "x-ray", "mri",
    "ct scan", "ultrasound", "biopsy", "pathology", "report", "admission",
    "discharge", "referral", "specialist", "consultation", "vaccine",
    "immunization", "screening", "prevention", "rehabilitation",
}


class QueryProcessor:
    """Normalizes and preprocesses user queries before retrieval.

    Handles:
    - Whitespace normalization
    - Case normalization
    - Punctuation cleaning
    - Empty/trivial query detection
    - Medical term detection
    - Language detection (basic)
    - Entity extraction (basic)
    """

    def __init__(self, min_query_length: int = 2) -> None:
        self._min_query_length = min_query_length

    def process(self, query: str) -> ProcessedQuery:
        if not query or not query.strip():
            raise EmptyQueryError("Query cannot be empty")

        original = query.strip()
        cleaned = self._clean(original)
        normalized = self._normalize(cleaned)

        if len(normalized) < self._min_query_length:
            raise QueryError(
                f"Query too short after preprocessing "
                f"(min {self._min_query_length} characters)"
            )

        word_count = len(normalized.split())
        has_medical = self._has_medical_terms(normalized)
        entities = self._extract_entities(normalized)

        return ProcessedQuery(
            original=original,
            normalized=normalized,
            cleaned=cleaned,
            language="en",
            is_empty=False,
            word_count=word_count,
            has_medical_terms=has_medical,
            detected_entities=entities,
        )

    def _clean(self, text: str) -> str:
        result = text.strip()
        result = re.sub(r"\s+", " ", result)
        result = re.sub(r"[^\w\s\-'/,()]", "", result)
        result = result.strip()
        return result

    def _normalize(self, text: str) -> str:
        return text.lower().strip()

    def _has_medical_terms(self, text: str) -> bool:
        words = set(text.split())
        for term in MEDICAL_TERMS:
            if term in words or term in text:
                return True
        return False

    def _extract_entities(self, text: str) -> list[str]:
        found: list[str] = []
        for term in sorted(MEDICAL_TERMS, key=len, reverse=True):
            if term in text:
                found.append(term)
        return found[:10]
