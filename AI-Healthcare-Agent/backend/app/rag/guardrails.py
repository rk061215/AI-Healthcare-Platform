from __future__ import annotations

import re
from typing import Any, Optional

from app.rag.exceptions import GuardrailError
from app.rag.models import GuardrailResult, RAGContext, RAGResponse


INSUFFICIENT_CONTEXT_PHRASES: list[str] = [
    "i don't have enough", "no information", "context does not",
    "not mentioned", "not provided", "cannot find", "not available",
    "insufficient", "unable to answer", "no data",
]

MEDICAL_DISCLAIMER = (
    "IMPORTANT: This information is for educational purposes only. "
    "Always consult your healthcare provider for medical advice."
)


class Guardrails:
    """Reusable guardrail layer for RAG pipeline.

    Pre-generation checks:
    - Insufficient context detection
    - Query safety validation

    Post-generation checks:
    - Unsupported claim detection
    - Hallucinated citation detection
    - Medical uncertainty flagging
    - Context grounding verification

    Designed so future safety policies can be added without modifying
    the RAG engine — add a new check method and register it.
    """

    def __init__(self, require_context_grounding: bool = True) -> None:
        self._require_grounding = require_context_grounding
        self._pre_checks: list[str] = [
            "check_insufficient_context",
            "check_query_safety",
        ]
        self._post_checks: list[str] = [
            "check_unsupported_claims",
            "check_medical_uncertainty",
            "check_citation_hallucination",
            "check_context_grounding",
        ]

    def check_pre_generation(
        self, query: str, context: RAGContext, **kwargs: Any
    ) -> GuardrailResult:
        """Run pre-generation guardrail checks.

        These checks run before the LLM is called.
        """
        warnings: list[str] = []
        failures: list[str] = []

        result = self._check_insufficient_context(context)
        if not result.passed:
            failures.extend(result.failures)
        warnings.extend(result.warnings)

        result = self._check_query_safety(query)
        if not result.passed:
            failures.extend(result.failures)
        warnings.extend(result.warnings)

        return GuardrailResult(
            passed=len(failures) == 0,
            score=self._compute_score(warnings, failures),
            warnings=warnings,
            failures=failures,
            requires_human_review=len(failures) > 0,
        )

    def check_post_generation(
        self,
        response: str,
        context: RAGContext,
        citations: Any = None,
        **kwargs: Any,
    ) -> GuardrailResult:
        """Run post-generation guardrail checks.

        These checks run after the LLM response is generated.
        """
        warnings: list[str] = []
        failures: list[str] = []

        result = self._check_unsupported_claims(response, context)
        if not result.passed:
            failures.extend(result.failures)
        warnings.extend(result.warnings)

        result = self._check_medical_uncertainty(response)
        if not result.passed:
            warnings.extend(result.warnings)

        result = self._check_citation_hallucination(response, citations)
        if not result.passed:
            failures.extend(result.failures)
        warnings.extend(result.warnings)

        if self._require_grounding:
            result = self._check_context_grounding(response, context)
            if not result.passed:
                warnings.extend(result.warnings)

        return GuardrailResult(
            passed=len(failures) == 0,
            score=self._compute_score(warnings, failures),
            warnings=warnings,
            failures=failures,
            requires_human_review=len(failures) > 0,
        )

    def apply_safety_disclaimer(self, response: str) -> str:
        """Append a medical disclaimer to the response."""
        return response + f"\n\n{MEDICAL_DISCLAIMER}"

    def _check_insufficient_context(self, context: RAGContext) -> GuardrailResult:
        warnings: list[str] = []
        failures: list[str] = []

        if not context.context or not context.context.strip():
            failures.append("No context available to answer the query")
        elif not context.has_sufficient_context:
            warnings.append("Context may be insufficient for a complete answer")
        elif context.fragment_count < 2:
            warnings.append("Very few context fragments available")

        return GuardrailResult(
            passed=len(failures) == 0,
            warnings=warnings,
            failures=failures,
        )

    def _check_query_safety(self, query: str) -> GuardrailResult:
        warnings: list[str] = []
        failures: list[str] = []

        harmful_patterns = [
            (r"(?i)\b(how to (harm|hurt|kill|injure|overdose))\b", "Self-harm query detected"),
            (r"(?i)\b(suicide|self.?harm|self.?destruct)\b", "Self-harm keyword detected"),
        ]

        for pattern, message in harmful_patterns:
            if re.search(pattern, query):
                failures.append(message)

        return GuardrailResult(
            passed=len(failures) == 0,
            warnings=warnings,
            failures=failures,
        )

    def _check_unsupported_claims(
        self, response: str, context: RAGContext
    ) -> GuardrailResult:
        warnings: list[str] = []
        failures: list[str] = []

        diagnostic_patterns = [
            r"(?i)\byou have\b",
            r"(?i)\byou are diagnosed with\b",
            r"(?i)\byour diagnosis is\b",
            r"(?i)\bi diagnose you with\b",
        ]

        for pattern in diagnostic_patterns:
            if re.search(pattern, response):
                warnings.append(
                    "Response may contain diagnostic language. "
                    "Medical diagnosis should not be provided."
                )

        treatment_patterns = [
            r"(?i)\byou should take\b",
            r"(?i)\b(i recommend|i prescribe)\b",
            r"(?i)\bchange your (medication|dosage|dose)\b",
            r"(?i)\bstop taking\b",
        ]

        for pattern in treatment_patterns:
            if re.search(pattern, response):
                warnings.append(
                    "Response may contain treatment recommendations. "
                    "Treatment changes should only be made by a doctor."
                )

        return GuardrailResult(
            passed=len(failures) == 0,
            warnings=warnings,
            failures=failures,
        )

    def _check_medical_uncertainty(self, response: str) -> GuardrailResult:
        warnings: list[str] = []

        overconfidence_patterns = [
            r"(?i)\bdefinitely\b",
            r"(?i)\bwithout a doubt\b",
            r"(?i)\b100% (certain|sure|guaranteed)\b",
            r"(?i)\balways (true|correct|right)\b",
        ]

        for pattern in overconfidence_patterns:
            if re.search(pattern, response):
                warnings.append(
                    "Response may express overconfidence. "
                    "Medical information should include appropriate uncertainty."
                )

        missing_uncertainty = True
        uncertainty_patterns = [
            r"(?i)\bbased on\b",
            r"(?i)\baccording to\b",
            r"(?i)\bthe context suggests\b",
            r"(?i)\bthe information provided\b",
            r"(?i)\bconsult your doctor\b",
        ]

        for pattern in uncertainty_patterns:
            if re.search(pattern, response):
                missing_uncertainty = False
                break

        if missing_uncertainty:
            warnings.append(
                "Response lacks explicit uncertainty qualifiers. "
                "Medical information should acknowledge limitations."
            )

        return GuardrailResult(
            passed=True,
            warnings=warnings,
            failures=[],
        )

    def _check_citation_hallucination(
        self, response: str, citations: Any
    ) -> GuardrailResult:
        warnings: list[str] = []
        failures: list[str] = []

        if citations is None:
            return GuardrailResult(passed=True, warnings=[], failures=[])

        valid_ids: set[str] = set()
        if hasattr(citations, "citations"):
            valid_ids = {str(c.citation_id) for c in citations.citations}
        elif isinstance(citations, (list, tuple)):
            valid_ids = set()

        pattern = re.compile(r"\[citation:(\d+)\]")
        for match in pattern.finditer(response):
            cited_id = match.group(1)
            if cited_id not in valid_ids:
                failures.append(
                    f"Hallucinated citation [{cited_id}] not found in sources"
                )

        return GuardrailResult(
            passed=len(failures) == 0,
            warnings=warnings,
            failures=failures,
        )

    def _check_context_grounding(
        self, response: str, context: RAGContext
    ) -> GuardrailResult:
        warnings: list[str] = []

        if not context.context:
            return GuardrailResult(passed=True, warnings=warnings, failures=[])

        response_lower = response.lower()
        context_lower = context.context.lower()

        if len(response_lower) > 50:
            overlap = self._compute_text_overlap(response_lower, context_lower)
            if overlap < 0.1:
                warnings.append(
                    "Response has very low overlap with context. "
                    "It may not be grounded in the provided documents."
                )

        return GuardrailResult(
            passed=True,
            warnings=warnings,
            failures=[],
        )

    def _compute_text_overlap(self, text_a: str, text_b: str) -> float:
        words_a = set(text_a.split())
        words_b = set(text_b.split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        return len(intersection) / len(words_a)

    def _compute_score(
        self, warnings: list[str], failures: list[str]
    ) -> float:
        base = 1.0
        base -= len(failures) * 0.4
        base -= len(warnings) * 0.15
        return max(base, 0.0)
