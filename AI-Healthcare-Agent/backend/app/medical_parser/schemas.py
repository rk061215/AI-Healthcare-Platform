from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

from app.medical_parser.types import ConfidenceLevel, DocumentType, SourceType

T = TypeVar("T")

SCHEMA_VERSION = "1.0"
EXTRACTION_VERSION_INITIAL = 1


class NormalizationMeta(BaseModel):
    original_value: str
    normalized_value: str
    normalization_rule: str


class ConfidenceField(BaseModel, Generic[T]):
    value: T
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    is_flagged: bool = False
    flag_reason: Optional[str] = None
    source: SourceType = SourceType.DEFAULT
    normalization: Optional[NormalizationMeta] = None


@dataclass
class ExtractionContext:
    """Carries per-field metadata through the parsing pipeline.

    Populated by Extractor, consumed by ConfidenceEngine.
    """
    source: SourceType = SourceType.DEFAULT
    raw_ai_response: Optional[str] = None
    field_sources: dict[str, SourceType] = field(default_factory=dict)
    field_normalizations: dict[str, NormalizationMeta] = field(default_factory=dict)
    validation_errors: list[str] = field(default_factory=list)


class FlaggedField(BaseModel):
    field_name: str
    reason: str
    confidence: float
    level: ConfidenceLevel


class MedicationExtracted(BaseModel):
    name: str = ""
    dosage: str = ""
    frequency: str = ""
    duration: str = ""
    route: str = ""
    instructions: str = ""


class LabResultExtracted(BaseModel):
    test_name: str = ""
    value: str = ""
    unit: str = ""
    reference_range: str = ""


class MedicalReportSchema(BaseModel):
    document_type: str = "PRESCRIPTION"
    patient_name: str = ""
    date_of_birth: str = ""
    document_date: str = ""
    doctor_name: str = ""
    hospital_name: str = ""
    diagnosis: str = ""
    medications: list[MedicationExtracted] = Field(default_factory=list)
    lab_results: list[LabResultExtracted] = Field(default_factory=list)
    follow_up_date: str = ""
    doctor_instructions: str = ""
    notes: str = ""


class MedicationResult(BaseModel):
    name: ConfidenceField[str]
    dosage: ConfidenceField[str]
    frequency: ConfidenceField[str]
    duration: ConfidenceField[str]
    route: ConfidenceField[str]
    instructions: ConfidenceField[str]


class LabResultResult(BaseModel):
    test_name: ConfidenceField[str]
    value: ConfidenceField[str]
    unit: ConfidenceField[str]
    reference_range: ConfidenceField[str]


class MedicalReportResult(BaseModel):
    schema_version: str = SCHEMA_VERSION
    extraction_version: int = EXTRACTION_VERSION_INITIAL
    extracted_at: Optional[datetime] = None

    document_type: DocumentType = DocumentType.PRESCRIPTION

    overall_ocr_confidence: float = 0.0
    overall_confidence: float = 0.0

    patient_name: Optional[ConfidenceField[str]] = None
    date_of_birth: Optional[ConfidenceField[str]] = None
    document_date: Optional[ConfidenceField[str]] = None
    doctor_name: Optional[ConfidenceField[str]] = None
    hospital_name: Optional[ConfidenceField[str]] = None
    diagnosis: Optional[ConfidenceField[str]] = None
    medications: list[MedicationResult] = Field(default_factory=list)
    lab_results: list[LabResultResult] = Field(default_factory=list)
    follow_up_date: Optional[ConfidenceField[str]] = None
    doctor_instructions: Optional[ConfidenceField[str]] = None

    flagged_fields: list[FlaggedField] = Field(default_factory=list)

    used_fallback: bool = False
    fallback_reason: Optional[str] = None

    confidence_debug: Optional[dict] = None
