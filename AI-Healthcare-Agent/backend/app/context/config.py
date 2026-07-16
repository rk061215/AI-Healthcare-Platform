from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContextConfig:
    max_tokens: int = 4000
    min_score_threshold: float = 0.0
    preserve_medical_sections: bool = True
    enable_dedup: bool = True
    enable_compression: bool = True
    enable_ranking: bool = True
    enable_citations: bool = True
    strategy: str = "priority_truncation"
    overlap_threshold_chars: int = 50
    section_order: tuple[str, ...] = (
        "chief_complaint",
        "history",
        "medication",
        "assessment",
        "diagnosis",
        "plan",
        "results",
        "summary",
    )
    priority_sections: tuple[str, ...] = (
        "diagnosis",
        "assessment",
        "medication",
        "plan",
    )
    default_priority_fields: tuple[str, ...] = (
        "diagnosis",
        "medication",
        "plan",
        "assessment",
    )
