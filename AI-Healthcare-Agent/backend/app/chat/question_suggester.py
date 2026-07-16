from __future__ import annotations

from typing import Any, Optional

from app.chat.models import SuggestedQuestion

QUESTION_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "diagnosis": [
        {"question": "Explain my diagnosis.", "category": "diagnosis", "priority": 1},
        {"question": "What are the key findings of my diagnosis?", "category": "diagnosis", "priority": 2},
        {"question": "What does my diagnosis mean?", "category": "diagnosis", "priority": 3},
    ],
    "medication": [
        {"question": "What medicines are prescribed?", "category": "medication", "priority": 1},
        {"question": "What are the dosages for my medicines?", "category": "medication", "priority": 2},
        {"question": "Are there any side effects I should know?", "category": "medication", "priority": 3},
    ],
    "lab_result": [
        {"question": "What do my lab results mean?", "category": "lab_result", "priority": 1},
        {"question": "Are any of my lab results abnormal?", "category": "lab_result", "priority": 2},
        {"question": "What is the trend in my lab results?", "category": "lab_result", "priority": 3},
    ],
    "follow_up": [
        {"question": "When is my next follow-up?", "category": "follow_up", "priority": 1},
        {"question": "What precautions should I take?", "category": "follow_up", "priority": 2},
        {"question": "What follow-up instructions were given?", "category": "follow_up", "priority": 3},
    ],
    "summary": [
        {"question": "Summarize this medical report.", "category": "summary", "priority": 1},
        {"question": "What are the most important points in my report?", "category": "summary", "priority": 2},
    ],
}

UNIVERSAL_QUESTIONS: list[dict[str, Any]] = [
    {"question": "What do I need to know about my health?", "category": "general", "priority": 4},
    {"question": "What should I ask my doctor?", "category": "general", "priority": 5},
]


class QuestionSuggester:
    """Generates suggested questions from document content.

    Rule-based: analyzes document sections to determine which question
    templates are relevant. Does NOT use the LLM for suggestion generation.

    Questions are prioritized: specific (diagnosis, medication) first,
    then general.
    """

    def __init__(self, max_suggestions: int = 5) -> None:
        self._max_suggestions = max_suggestions

    def suggest(
        self,
        document_sections: Optional[list[str]] = None,
        recent_questions: Optional[list[str]] = None,
        document_has_diagnosis: bool = False,
        document_has_medication: bool = False,
        document_has_lab_results: bool = False,
        document_has_follow_up: bool = False,
    ) -> list[SuggestedQuestion]:
        candidates: list[dict[str, Any]] = []

        if document_has_diagnosis:
            candidates.extend(QUESTION_TEMPLATES["diagnosis"])
        if document_has_medication:
            candidates.extend(QUESTION_TEMPLATES["medication"])
        if document_has_lab_results:
            candidates.extend(QUESTION_TEMPLATES["lab_result"])
        if document_has_follow_up:
            candidates.extend(QUESTION_TEMPLATES["follow_up"])

        has_any_section = (
            document_has_diagnosis
            or document_has_medication
            or document_has_lab_results
            or document_has_follow_up
        )
        if has_any_section or document_sections:
            candidates.extend(QUESTION_TEMPLATES["summary"])

        if not candidates:
            candidates.extend(UNIVERSAL_QUESTIONS)

        candidates.sort(key=lambda x: x.get("priority", 99))

        seen_questions = set()
        if recent_questions:
            seen_questions.update(q.lower().strip().rstrip("?") for q in recent_questions)

        result: list[SuggestedQuestion] = []
        for c in candidates:
            q_lower = c["question"].lower().strip().rstrip("?")
            if q_lower in seen_questions:
                continue
            result.append(SuggestedQuestion(**c))
            seen_questions.add(q_lower)
            if len(result) >= self._max_suggestions:
                break

        return result

    def suggest_from_sections(
        self, sections: list[str]
    ) -> list[SuggestedQuestion]:
        sections_lower = [s.lower() for s in sections]
        has_diag = any(
            "diagnosis" in s or "assessment" in s for s in sections_lower
        )
        has_med = any(
            "medication" in s or "prescription" in s or "medicine" in s
            for s in sections_lower
        )
        has_lab = any(
            "lab" in s or "result" in s or "test" in s for s in sections_lower
        )
        has_fup = any(
            "follow" in s or "plan" in s or "next" in s
            for s in sections_lower
        )

        return self.suggest(
            document_sections=sections,
            document_has_diagnosis=has_diag,
            document_has_medication=has_med,
            document_has_lab_results=has_lab,
            document_has_follow_up=has_fup,
        )
