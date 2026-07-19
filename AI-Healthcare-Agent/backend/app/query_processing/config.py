from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QueryUnderstandingConfig:
    provider: str = "gemini"
    model: str = "gemini-2.0-flash"
    temperature: float = 0.2
    max_tokens: int = 512
    enable_llm_understanding: bool = True
    enable_entity_extraction: bool = True
    enable_question_decomposition: bool = True
    extractor_confidence_threshold: float = 0.4
    max_sub_questions: int = 5
    min_query_length: int = 2
    understanding_prompt_template: Optional[str] = None
    entity_types: list[str] = field(default_factory=lambda: [
        "medication", "dosage", "lab_value", "condition",
        "symptom", "anatomy", "procedure", "patient_demographic",
    ])
