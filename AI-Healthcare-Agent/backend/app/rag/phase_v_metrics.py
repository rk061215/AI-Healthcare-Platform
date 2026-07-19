from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class QueryUnderstandingMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    processing_time_ms: float = 0.0
    intent_detected: str = "unknown"
    entities_extracted: int = 0
    sub_questions_generated: int = 0
    confidence: float = 0.0
    provider: str = "rule_based"


class RetrievalMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    processing_time_ms: float = 0.0
    strategy: str = "vector"
    total_results: int = 0
    returned_results: int = 0
    reranking_time_ms: float = 0.0
    fusion_strategy: Optional[str] = None
    num_queries: int = 1


class ContextMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    processing_time_ms: float = 0.0
    input_fragments: int = 0
    after_dedup: int = 0
    after_compression: int = 0
    final_tokens: int = 0
    max_tokens_budget: int = 4000
    truncated: bool = False


class CitationMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    processing_time_ms: float = 0.0
    total_citations: int = 0
    avg_relevance: float = 0.0
    coverage_score: float = 0.0
    has_contradictions: bool = False
    groups_count: int = 0


class ConfidenceMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    processing_time_ms: float = 0.0
    overall_confidence: float = 0.0
    citation_coverage: float = 0.0
    source_quality: float = 0.0
    claim_support: float = 0.0
    hallucination_risk: float = 0.0
    completeness: float = 0.0
    requires_human_review: bool = False


class SafetyMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    processing_time_ms: float = 0.0
    input_safe: bool = True
    output_safe: bool = True
    pii_detected: bool = False
    medical_safe: bool = True
    blocked_terms_found: list[str] = Field(default_factory=list)


class PlannerMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    processing_time_ms: float = 0.0
    steps_planned: int = 0
    tool_calls_planned: int = 0
    retrieval_steps: int = 0


class ReflectionMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    processing_time_ms: float = 0.0
    score: float = 0.0
    issues_found: int = 0
    high_severity_issues: int = 0
    refinements_applied: bool = False


class PhaseVOverallMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_understanding: QueryUnderstandingMetrics = Field(default_factory=QueryUnderstandingMetrics)
    retrieval: RetrievalMetrics = Field(default_factory=RetrievalMetrics)
    context: ContextMetrics = Field(default_factory=ContextMetrics)
    citation: CitationMetrics = Field(default_factory=CitationMetrics)
    confidence: ConfidenceMetrics = Field(default_factory=ConfidenceMetrics)
    safety: SafetyMetrics = Field(default_factory=SafetyMetrics)
    planner: PlannerMetrics = Field(default_factory=PlannerMetrics)
    reflection: ReflectionMetrics = Field(default_factory=ReflectionMetrics)
    total_processing_time_ms: float = 0.0
    pipeline_version: str = "5.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
