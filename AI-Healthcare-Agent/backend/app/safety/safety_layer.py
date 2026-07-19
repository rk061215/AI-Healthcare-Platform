from __future__ import annotations

import re
import time
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.safety.config import SafetyConfig
from app.safety.exceptions import UnsafeContentError
from app.safety.pii_filter import PIIFilter


class SafetyCheckResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool = True
    input_safe: bool = True
    output_safe: bool = True
    pii_detected: bool = False
    medical_safe: bool = True
    blocked_terms_found: list[str] = Field(default_factory=list)
    pii_redacted: bool = False
    warnings: list[str] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)
    processing_time_ms: float = 0.0


class SafetyLayer:
    def __init__(
        self,
        config: Optional[SafetyConfig] = None,
        pii_filter: Optional[PIIFilter] = None,
    ):
        self._config = config or SafetyConfig()
        self._pii_filter = pii_filter or PIIFilter(
            enabled=self._config.enable_pii_filtering
        )

    def check_input(self, text: str) -> SafetyCheckResult:
        start = time.perf_counter()
        result = SafetyCheckResult()

        if not self._config.enable_input_safety:
            elapsed = (time.perf_counter() - start) * 1000
            result.processing_time_ms = round(elapsed, 2)
            return result

        if not text or not text.strip():
            result.passed = False
            result.input_safe = False
            result.failures.append("Empty input")
            elapsed = (time.perf_counter() - start) * 1000
            result.processing_time_ms = round(elapsed, 2)
            return result

        if len(text) > self._config.max_input_length:
            result.passed = False
            result.input_safe = False
            result.failures.append(f"Input exceeds max length ({len(text)} > {self._config.max_input_length})")
            elapsed = (time.perf_counter() - start) * 1000
            result.processing_time_ms = round(elapsed, 2)
            return result

        blocked = self._check_blocked_terms(text)
        if blocked:
            result.passed = False
            result.input_safe = False
            result.blocked_terms_found = blocked
            result.failures.append("Blocked terms detected in input")

        pii = self._pii_filter.detect(text)
        if pii:
            result.pii_detected = True
            result.warnings.append(f"PII detected: {[p['type'] for p in pii]}")

        elapsed = (time.perf_counter() - start) * 1000
        result.processing_time_ms = round(elapsed, 2)
        return result

    def check_output(
        self, text: str, original_input: Optional[str] = None
    ) -> SafetyCheckResult:
        start = time.perf_counter()
        result = SafetyCheckResult()

        if not self._config.enable_output_safety:
            elapsed = (time.perf_counter() - start) * 1000
            result.processing_time_ms = round(elapsed, 2)
            return result

        if len(text) > self._config.max_output_length:
            result.output_safe = False
            result.warnings.append(f"Output truncated (>{self._config.max_output_length} chars)")

        if self._config.enable_medical_safety:
            medical_ok = self._check_medical_safety(text)
            if not medical_ok:
                result.medical_safe = False
                result.warnings.append("Medical safety advisory — response should include disclaimer")

        if self._config.enable_pii_filtering:
            if self._pii_filter.contains_pii(text):
                result.pii_detected = True
                result.warnings.append("PII detected in output")

        result.passed = result.output_safe and result.medical_safe

        elapsed = (time.perf_counter() - start) * 1000
        result.processing_time_ms = round(elapsed, 2)
        return result

    def sanitize_output(self, text: str) -> str:
        result = self._pii_filter.filter(text)

        if self._config.enable_medical_safety:
            disclaimer = self._config.medical_disclaimer
            if disclaimer not in result:
                result = result.rstrip() + f"\n\n{disclaimer}"

        return result

    def _check_blocked_terms(self, text: str) -> list[str]:
        text_lower = text.lower()
        found: list[str] = []
        for term in self._config.blocked_terms:
            if term.lower() in text_lower:
                found.append(term)
        return found

    def _check_medical_safety(self, text: str) -> bool:
        text_lower = text.lower()
        unsafe_patterns = [
            r"\b(always|never)\s+",
            r"\bguaranteed?\s+(cure|treatment|result)",
            r"\b(100%|one.hundred.percent)\s+(cure|effective|safe)",
            r"\breplace.*medical.*advice\b",
            r"\b(ignore|stop|discontinue)\s+(medication|treatment|therapy)\s+(without|unless)",
        ]
        for pattern in unsafe_patterns:
            if re.search(pattern, text_lower):
                return False
        return True
