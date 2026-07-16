from __future__ import annotations

import enum


class DocumentType(str, enum.Enum):
    PRESCRIPTION = "prescription"
    LAB_REPORT = "lab_report"
    DISCHARGE_SUMMARY = "discharge_summary"
    RADIOLOGY_REPORT = "radiology_report"
    BLOOD_TEST = "blood_test"
    XRAY = "xray"
    MRI = "mri"
    CT_SCAN = "ct_scan"
    GENERAL = "general"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SourceType(str, enum.Enum):
    AI = "AI"
    REGEX = "REGEX"
    OCR = "OCR"
    DEFAULT = "DEFAULT"
    USER = "USER"


CONFIDENCE_THRESHOLD_HIGH: float = 0.90
CONFIDENCE_THRESHOLD_MEDIUM: float = 0.75
