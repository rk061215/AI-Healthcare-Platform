from __future__ import annotations

import re
from typing import Optional

from app.rag.exceptions import QueryClassificationError
from app.rag.models import QueryClassification


CLASSIFICATION_PATTERNS: dict[str, list[re.Pattern]] = {
    "medication": [
        re.compile(r"\b(medication|medicine|drug|prescription|dosage|dose|take|pill|tablet|capsule|syrup|injection)\b", re.I),
        re.compile(r"\b(how (often|many|much|long).*(take|use|medication|medicine|drug))\b", re.I),
        re.compile(r"\b(what (medication|medicine|drug).*prescribed)\b", re.I),
        re.compile(r"\b(side.effect|interaction|allergic|contraindication)\b", re.I),
        re.compile(r"\b(when.*take|before.*meal|after.*food|empty.stomach)\b", re.I),
    ],
    "lab_result": [
        re.compile(r"\b(lab|test|result|blood|urine|cholesterol|glucose|hemoglobin|a1c|lipid|panel)\b", re.I),
        re.compile(r"\b(lab.result|test.result|blood.work|blood.test|lab.work)\b", re.I),
        re.compile(r"\b(what (do|does).* (test|lab|result).*(mean|show|indicate))\b", re.I),
        re.compile(r"\b(level|range|normal|abnormal|elevated|high|low)\b", re.I),
        re.compile(r"\b(mg/dl|mmol|l/dl|units/l)\b", re.I),
    ],
    "diagnosis": [
        re.compile(r"\b(diagnosis|diagnose|condition|disease|disorder|syndrome)\b", re.I),
        re.compile(r"\b(what (is|was|were).*(diagnosis|diagnosed|condition))\b", re.I),
        re.compile(r"\b(do (i|I).*have|am (i|I).*diagnosed|was (i|I).*told)\b", re.I),
        re.compile(r"\b(explain.*(diagnosis|condition|disease))\b", re.I),
    ],
    "follow_up": [
        re.compile(r"\b(follow.up|next (visit|appointment|checkup|check.up|review))\b", re.I),
        re.compile(r"\b(when.*(see|visit|follow.up|come.back|return))\b", re.I),
        re.compile(r"\b(appointment|schedule|reschedule|book)\b", re.I),
        re.compile(r"\b(how.long.*(recover|heal|monitor|watch))\b", re.I),
    ],
    "patient_metadata": [
        re.compile(r"\b(my|mine)\s+(name|age|date.of.birth|dob|address|phone|contact|height|weight|bmi)\b", re.I),
        re.compile(r"\b(what.*my.*(name|age|dob|height|weight|blood.type))\b", re.I),
        re.compile(r"\b(who is my doctor|who.*treating|primary.care)\b", re.I),
        re.compile(r"\b(admission|discharge) (date|day|when)\b", re.I),
    ],
    "general_medical": [
        re.compile(r"\b(explain|describe|tell me about|what is|define)\b", re.I),
        re.compile(r"\b(how does|why (do|does)|what causes|what happens)\b", re.I),
        re.compile(r"\b(should (i|I)|can (i|I)|is it (safe|ok|normal))\b", re.I),
        re.compile(r"\b(difference|compare|vs|versus|alternative|option)\b", re.I),
    ],
}


CLASSIFICATION_PRIORITY: list[str] = [
    "medication",
    "lab_result",
    "diagnosis",
    "follow_up",
    "patient_metadata",
    "general_medical",
]


class QueryClassifier:
    """Classifies user queries into medical categories.

    Initial implementation is rule-based using regex patterns.
    Designed so an AI classifier can replace it later:
    - Same interface (classify() -> QueryClassification)
    - Same output model
    - Swap via config or dependency injection
    """

    def __init__(self, confidence_threshold: float = 0.3) -> None:
        self._threshold = confidence_threshold

    def classify(self, query: str) -> QueryClassification:
        """Classify the query into a medical question type.

        Returns QueryClassification with the best-matching category
        and optional sub-questions or suggested retrieval parameters.
        """
        if not query or not query.strip():
            raise QueryClassificationError("Cannot classify empty query")

        scores: dict[str, float] = {}
        matched_patterns: dict[str, int] = {}

        for qtype, patterns in CLASSIFICATION_PATTERNS.items():
            score = 0.0
            match_count = 0
            for pattern in patterns:
                matches = pattern.findall(query)
                if matches:
                    score += len(matches) * 0.25
                    match_count += len(matches)
            if match_count > 0:
                scores[qtype] = score
                matched_patterns[qtype] = match_count

        if not scores:
            return QueryClassification(query_type="unknown", confidence=0.0)

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        total_score = sum(scores.values())
        confidence = min(best_score / max(total_score, 0.01), 1.0)

        suggested_top_k = self._suggest_top_k(best_type)
        suggested_sections = self._suggest_sections(best_type)

        return QueryClassification(
            query_type=best_type,
            confidence=round(confidence, 4),
            sub_questions=self._generate_sub_questions(best_type, query),
            requires_patient_context=self._needs_patient_context(best_type),
            requires_recent_docs=self._needs_recent_docs(best_type),
            suggested_top_k=suggested_top_k,
            suggested_sections=suggested_sections,
        )

    def _suggest_top_k(self, query_type: str) -> int:
        suggestions = {
            "medication": 15,
            "lab_result": 10,
            "diagnosis": 10,
            "follow_up": 8,
            "patient_metadata": 5,
            "general_medical": 10,
        }
        return suggestions.get(query_type, 10)

    def _suggest_sections(self, query_type: str) -> list[str]:
        suggestions = {
            "medication": ["medication", "prescription", "plan"],
            "lab_result": ["lab_results", "results"],
            "diagnosis": ["diagnosis", "assessment", "summary"],
            "follow_up": ["follow_up", "plan", "summary"],
            "patient_metadata": ["patient_information"],
            "general_medical": ["diagnosis", "medication", "doctor_notes"],
        }
        return suggestions.get(query_type, [])

    def _needs_patient_context(self, query_type: str) -> bool:
        return query_type != "general_medical"

    def _needs_recent_docs(self, query_type: str) -> bool:
        return query_type in ("lab_result", "medication")

    def _generate_sub_questions(
        self, query_type: str, query: str
    ) -> list[str]:
        sub_map: dict[str, list[str]] = {
            "medication": [
                "What medications are prescribed?",
                "What are the dosages and frequencies?",
            ],
            "lab_result": [
                "What lab tests were performed?",
                "What were the results and reference ranges?",
            ],
            "diagnosis": [
                "What is the diagnosis?",
                "What are the key findings?",
            ],
            "follow_up": [
                "When is the next appointment?",
                "What follow-up instructions were given?",
            ],
            "patient_metadata": [
                "What patient information is available?",
            ],
            "general_medical": [],
        }
        return sub_map.get(query_type, [])
