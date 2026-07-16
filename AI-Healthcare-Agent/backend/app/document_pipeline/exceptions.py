from __future__ import annotations


class DocumentPipelineError(Exception):
    """Base exception for the document pipeline."""


class PipelineConfigurationError(DocumentPipelineError):
    """Raised when pipeline configuration is invalid."""


class DocumentCleanError(DocumentPipelineError):
    """Raised when document cleaning fails."""


class ChunkingError(DocumentPipelineError):
    """Raised when chunking fails."""


class MetadataExtractionError(DocumentPipelineError):
    """Raised when metadata extraction fails."""


class SectionDetectionError(DocumentPipelineError):
    """Raised when section detection fails."""


class EmptyDocumentError(DocumentPipelineError):
    """Raised when the document is empty after cleaning."""


class MalformedDocumentError(DocumentPipelineError):
    """Raised when the document is malformed and cannot be processed."""


class VersionTrackingError(DocumentPipelineError):
    """Raised when version tracking fails."""


class ClassificationError(DocumentPipelineError):
    """Raised when document classification fails."""


class StageExecutionError(DocumentPipelineError):
    """Raised when a pipeline stage fails to execute."""
