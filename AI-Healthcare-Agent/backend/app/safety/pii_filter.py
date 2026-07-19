from __future__ import annotations

import re
from typing import Optional

PII_PATTERNS: dict[str, re.Pattern] = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "credit_card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
    "passport": re.compile(r"\b[A-Z]{1}\d{8}\b"),
    "medicare_id": re.compile(r"\b\d{3}-\d{2}-\d{4}[A-Z]\b"),
}

REDACTION_TOKEN = "[REDACTED]"


class PIIFilter:
    def __init__(self, enabled: bool = True, redaction_token: str = REDACTION_TOKEN):
        self._enabled = enabled
        self._token = redaction_token

    def filter(self, text: str) -> str:
        if not self._enabled or not text:
            return text

        result = text
        for pii_type, pattern in PII_PATTERNS.items():
            result = pattern.sub(self._token, result)

        return result

    def detect(self, text: str) -> list[dict[str, object]]:
        if not text:
            return []

        detections: list[dict[str, object]] = []
        for pii_type, pattern in PII_PATTERNS.items():
            for match in pattern.finditer(text):
                detections.append({
                    "type": pii_type,
                    "value": match.group(0),
                    "position": match.start(),
                })
        return detections

    def contains_pii(self, text: str) -> bool:
        for pattern in PII_PATTERNS.values():
            if pattern.search(text):
                return True
        return False
