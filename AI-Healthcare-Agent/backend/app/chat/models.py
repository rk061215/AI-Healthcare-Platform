from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

CHAT_SCHEMA_VERSION = "1.0.0"


class QuestionType(str, Enum):
    general = "general"
    diagnosis = "diagnosis"
    medication = "medication"
    lab_result = "lab_result"
    follow_up = "follow_up"
    summary = "summary"
    precaution = "precaution"


class ConfidenceLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    insufficient_evidence = "insufficient_evidence"


class ConfidenceScore(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall: float = 0.0
    level: ConfidenceLevel = ConfidenceLevel.insufficient_evidence
    retrieval_score: float = 0.0
    chunk_count: int = 0
    citation_coverage: float = 0.0
    guardrail_validated: bool = False
    insufficient_evidence: bool = False


class SuggestedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    category: str = "general"
    priority: int = 0


class QAPair(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    query_type: str = "unknown"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0


class ChatSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: datetime = Field(default_factory=datetime.utcnow)
    document_id: Optional[str] = None
    report_id: Optional[str] = None
    document_type: Optional[str] = None
    document_sections: list[str] = Field(default_factory=list)
    document_has_diagnosis: bool = False
    document_has_medication: bool = False
    document_has_lab_results: bool = False
    document_has_follow_up: bool = False
    questions: list[QAPair] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    session_id: Optional[str] = None
    patient_id: Optional[str] = None
    report_id: Optional[str] = None
    document_type: Optional[str] = None
    document_sections: Optional[list[str]] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_k: Optional[int] = None
    enable_citations: bool = True


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    confidence: ConfidenceScore = Field(default_factory=ConfidenceScore)
    suggested_questions: list[SuggestedQuestion] = Field(default_factory=list)
    session_id: str = ""
    query_type: str = "unknown"
    is_follow_up: bool = False
    timing_breakdown: dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: float = 0.0
    schema_version: str = CHAT_SCHEMA_VERSION
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_type: str = ""
    sections: list[str] = Field(default_factory=list)
    key_findings: list[str] = Field(default_factory=list)
    has_diagnosis: bool = False
    has_medication: bool = False
    has_lab_results: bool = False
    has_follow_up_recommendations: bool = False
