from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.document_pipeline.config import DocumentPipelineConfig
from app.document_pipeline.document import ProcessedDocument
from app.document_pipeline.chunk import DocumentChunk


class DocumentCleaner(ABC):
    """Interface for text cleaning strategies."""

    @abstractmethod
    def clean(self, text: str, config: Optional[DocumentPipelineConfig] = None) -> str:
        """Clean and normalize raw OCR text."""


class DocumentClassifier(ABC):
    """Interface for document type classification."""

    @abstractmethod
    def classify(self, text: str) -> str:
        """Classify the document into a type string (e.g. 'prescription', 'lab_report')."""


class SectionDetector(ABC):
    """Interface for detecting sections within medical documents."""

    @abstractmethod
    def detect_sections(self, text: str) -> dict[str, str]:
        """Return a dict mapping section headers to their text content."""


class Chunker(ABC):
    """Interface for document chunking strategies."""

    @abstractmethod
    def chunk(self, document: ProcessedDocument, config: DocumentPipelineConfig) -> list[DocumentChunk]:
        """Split a processed document into chunks."""


class MetadataExtractor(ABC):
    """Interface for metadata enrichment."""

    @abstractmethod
    def extract(self, document: ProcessedDocument, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Enrich chunks with metadata."""


class VersionTracker(ABC):
    """Interface for document and chunk version tracking."""

    @abstractmethod
    def get_document_version(self) -> str:
        """Return the current document processing version."""

    @abstractmethod
    def get_extraction_version(self) -> str:
        """Return the current extraction pipeline version."""

    @abstractmethod
    def get_schema_version(self) -> str:
        """Return the current chunk schema version."""

    @abstractmethod
    def get_embedding_version(self) -> str:
        """Return the current embedding schema version."""
