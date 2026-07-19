from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class UnderstandingIntent(str, Enum):
    factual = "factual"
    factoid = "factoid"
    informational = "informational"
    instructional = "instructional"
    comparative = "comparative"
    diagnostic = "diagnostic"
    prognostic = "prognostic"
    administrative = "administrative"
    exploratory = "exploratory"
    troubleshooting = "troubleshooting"
    unknown = "unknown"


class DecomposedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    intent: UnderstandingIntent = UnderstandingIntent.factual
    target_entities: list[str] = Field(default_factory=list)
    requires_retrieval: bool = True
    weight: float = 1.0


class UnderstandingResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original: str
    normalized: str
    language: str = "en"
    word_count: int = 0
    has_medical_terms: bool = False
    intent: UnderstandingIntent = UnderstandingIntent.unknown
    confidence: float = 0.0
    entities: list[dict[str, Any]] = Field(default_factory=list)
    sub_questions: list[DecomposedQuestion] = Field(default_factory=list)
    complexity: str = "simple"
    requires_patient_context: bool = True
    requires_recent_docs: bool = False
    suggested_top_k: int = 10
    suggested_sections: list[str] = Field(default_factory=list)
    processing_time_ms: float = 0.0
    provider: str = "rule_based"
    schema_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
