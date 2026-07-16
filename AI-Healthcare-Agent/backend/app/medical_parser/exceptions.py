from __future__ import annotations


class MedicalParserError(Exception):
    """Base exception for all medical parser errors."""


class ExtractorError(MedicalParserError):
    """Raised when extraction (AI or regex) fails."""


class AIExtractorError(ExtractorError):
    """Raised when the AI provider fails to return valid output."""


class RegexExtractorError(ExtractorError):
    """Raised when regex fallback extraction fails."""


class ValidationError(MedicalParserError):
    """Raised when extracted data fails validation."""


class EmptyOCRError(ValidationError):
    """Raised when OCR text is empty or whitespace-only."""


class MissingMandatoryFieldError(ValidationError):
    """Raised when a required field is missing after extraction."""


class InvalidAIContentError(ValidationError):
    """Raised when AI returns non-JSON or malformed content."""


class RetryExhaustedError(MedicalParserError):
    """Raised when all retry attempts are exhausted."""
