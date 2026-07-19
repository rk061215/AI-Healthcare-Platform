"""Query Understanding — advanced query analysis, entity extraction, and decomposition.

Provides a pluggable abstraction over query understanding that can use
rule-based, LLM-based, or hybrid strategies — all through the existing
AI provider abstraction (no vendor lock-in).
"""

from app.query_processing.base import BaseQueryUnderstander
from app.query_processing.config import QueryUnderstandingConfig
from app.query_processing.entity_extractor import (
    DosageInfo,
    ExtractedEntity,
    LabValueInfo,
    MedicalEntityExtractor,
    MedicationInfo,
)
from app.query_processing.exceptions import (
    DecompositionError,
    EntityExtractionError,
    QueryProcessingError,
    UnderstandingError,
)
from app.query_processing.llm_understander import LLMQueryUnderstander
from app.query_processing.models import (
    DecomposedQuestion,
    UnderstandingIntent,
    UnderstandingResult,
)
from app.query_processing.question_decomposer import QuestionDecomposer

__all__ = [
    "BaseQueryUnderstander",
    "LLMQueryUnderstander",
    "QueryUnderstandingConfig",
    "UnderstandingResult",
    "UnderstandingIntent",
    "DecomposedQuestion",
    "MedicalEntityExtractor",
    "ExtractedEntity",
    "MedicationInfo",
    "DosageInfo",
    "LabValueInfo",
    "QuestionDecomposer",
    "QueryProcessingError",
    "UnderstandingError",
    "EntityExtractionError",
    "DecompositionError",
]
