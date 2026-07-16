from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChatConfig:
    session_timeout_minutes: int = 30
    max_questions_per_session: int = 50
    max_suggested_questions: int = 5
    confidence_min_chunks: int = 2
    confidence_min_score: float = 0.5
    confidence_citation_coverage_min: float = 0.3
    enable_question_suggestions: bool = True
    enable_follow_up_detection: bool = True
    enable_unknown_answer_detection: bool = True
    default_top_k: int = 10
    default_temperature: float = 0.3
    default_max_tokens: int = 2048
