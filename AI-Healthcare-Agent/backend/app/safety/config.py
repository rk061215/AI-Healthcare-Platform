from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SafetyConfig:
    enable_input_safety: bool = True
    enable_output_safety: bool = True
    enable_pii_filtering: bool = True
    enable_medical_safety: bool = True
    max_input_length: int = 10000
    max_output_length: int = 50000
    blocked_terms: list[str] = field(default_factory=lambda: [
        "suicide", "self-harm", "self_harm", "selfharm",
    ])
    pii_patterns: list[str] = field(default_factory=lambda: [
        "ssn", "social.security", "credit.card", "passport",
    ])
    medical_disclaimer: str = (
        "This information is for educational purposes only. "
        "Always consult a healthcare professional for medical advice."
    )
