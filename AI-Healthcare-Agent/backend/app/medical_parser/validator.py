from __future__ import annotations

import re
import time as time_module
from dataclasses import dataclass, field
from typing import Callable, Optional

from app.medical_parser.exceptions import (
    InvalidAIContentError,
    MissingMandatoryFieldError,
    RetryExhaustedError,
    ValidationError,
)
from app.medical_parser.schemas import (
    ExtractionContext,
    MedicalReportSchema,
)


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_required: list[str] = field(default_factory=list)


REQUIRED_FIELDS: list[str] = [
    "patient_name",
    "diagnosis",
    "medications",
]

DATE_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}$"  # ISO 8601
    r"|^\d{2}/\d{2}/\d{4}$"  # MM/DD/YYYY
    r"|^\d{2}-\d{2}-\d{4}$"  # MM-DD-YYYY
    r"|^\d{4}/\d{2}/\d{2}$"  # YYYY/MM/DD
)


def validate(schema: MedicalReportSchema) -> ValidationResult:
    """Validate an extracted MedicalReportSchema.

    Pure function — does not call any external service.
    Returns a ValidationResult with errors, warnings, and missing required fields.
    """
    result = ValidationResult()

    _validate_required_fields(schema, result)
    _validate_document_type(schema, result)
    _validate_medications(schema, result)
    _validate_lab_results(schema, result)
    _validate_dates(schema, result)
    _validate_not_empty(schema, result)

    if result.errors:
        result.is_valid = False

    return result


def validate_with_retry(
    ocr_text: str,
    extract_fn: Callable[[], tuple[MedicalReportSchema, ExtractionContext]],
    max_retries: int = 3,
    retry_delay_seconds: float = 2.0,
) -> tuple[MedicalReportSchema, ExtractionContext, ValidationResult]:
    """Validate extraction results with retry on failure.

    Calls extract_fn, validates the result, and retries up to max_retries
    times if validation fails. Returns the first valid result or raises
    after exhausting retries.
    """
    last_result: Optional[ValidationResult] = None

    for attempt in range(max_retries):
        schema, context = extract_fn()

        vr = validate(schema)
        last_result = vr

        if vr.is_valid:
            return schema, context, vr

        if attempt < max_retries - 1:
            time_module.sleep(retry_delay_seconds * (2 ** attempt))

    raise RetryExhaustedError(
        f"Validation failed after {max_retries} attempts. "
        f"Errors: {'; '.join(last_result.errors) if last_result else 'unknown'}"
    )


def _validate_required_fields(schema: MedicalReportSchema, result: ValidationResult) -> None:
    for field_name in REQUIRED_FIELDS:
        value = getattr(schema, field_name, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            result.missing_required.append(field_name)
            result.errors.append(f"Required field '{field_name}' is missing or empty")
        elif isinstance(value, list) and len(value) == 0:
            if field_name == "medications":
                result.missing_required.append(field_name)
                result.errors.append("Required field 'medications' is empty — at least one medication expected")


def _validate_document_type(schema: MedicalReportSchema, result: ValidationResult) -> None:
    allowed_types = {
        "PRESCRIPTION", "LAB_REPORT", "DISCHARGE_SUMMARY",
        "RADIOLOGY_REPORT", "BLOOD_TEST", "XRAY", "MRI",
        "CT_SCAN", "GENERAL", "UNKNOWN",
    }
    if schema.document_type not in allowed_types:
        result.errors.append(
            f"Invalid document_type '{schema.document_type}'. "
            f"Must be one of: {', '.join(sorted(allowed_types))}"
        )


def _validate_medications(schema: MedicalReportSchema, result: ValidationResult) -> None:
    for i, med in enumerate(schema.medications):
        if not med.name.strip():
            result.errors.append(f"Medication at index {i} has empty name")
        if med.dosage and not _looks_like_dosage(med.dosage):
            result.warnings.append(
                f"Medication '{med.name or 'unnamed'}' dosage '{med.dosage}' "
                f"does not include a unit (mg, ml, mcg, etc.)"
            )


def _validate_lab_results(schema: MedicalReportSchema, result: ValidationResult) -> None:
    for i, lab in enumerate(schema.lab_results):
        if not lab.test_name.strip():
            result.errors.append(f"Lab result at index {i} has empty test_name")
        if lab.value and not lab.unit:
            result.warnings.append(
                f"Lab result '{lab.test_name}' has value '{lab.value}' but no unit"
            )


def _validate_dates(schema: MedicalReportSchema, result: ValidationResult) -> None:
    date_fields = [
        ("date_of_birth", schema.date_of_birth),
        ("document_date", schema.document_date),
        ("follow_up_date", schema.follow_up_date),
    ]
    for field_name, value in date_fields:
        if value and not DATE_PATTERN.match(value):
            result.warnings.append(
                f"Field '{field_name}' value '{value}' does not match expected date format "
                f"(ISO 8601: YYYY-MM-DD or MM/DD/YYYY)"
            )


def _validate_not_empty(schema: MedicalReportSchema, result: ValidationResult) -> None:
    all_empty = True
    string_fields = [
        schema.patient_name,
        schema.date_of_birth,
        schema.document_date,
        schema.doctor_name,
        schema.hospital_name,
        schema.diagnosis,
        schema.follow_up_date,
        schema.doctor_instructions,
    ]
    for val in string_fields:
        if val and val.strip():
            all_empty = False
            break

    if schema.medications:
        all_empty = False
    if schema.lab_results:
        all_empty = False

    if all_empty:
        result.errors.append(
            "All fields are empty — extraction produced no data"
        )


def _looks_like_dosage(value: str) -> bool:
    return bool(re.search(r"(mg|mcg|g|ml|cc|IU|units?|mEq|%)\b", value, re.IGNORECASE))
