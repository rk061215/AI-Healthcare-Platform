"""Provider-independent document processing pipeline.

Converts uploaded medical documents into clean, versioned, metadata-rich chunks
ready for embedding and indexing. No vector database dependency.

Architecture:
    DocumentPipeline (orchestrator)
      ├── DocumentCleaner (ABC) ← DefaultDocumentCleaner
      ├── DocumentClassifier (ABC) ← SimpleDocumentClassifier
      ├── SectionDetector (ABC) ← SimpleSectionDetector
      ├── Chunker (ABC) ← FixedSizeChunker, RecursiveChunker, SemanticChunker,
      │                     MedicalSectionChunker, SentenceChunker
      ├── MetadataExtractor (ABC) ← DefaultMetadataExtractor
      └── VersionTracker (ABC) ← DefaultVersionTracker

Pipeline flow:
    Input OCR Text
      → Clean (cleaner)
      → Classify (classifier)
      → Detect Sections (section_detector)
      → Chunk (chunker)
      → Enrich Metadata (metadata_extractor)
      → Output: list[DocumentChunk]
"""

from app.document_pipeline.chunk import ChunkMetadata, DocumentChunk
from app.document_pipeline.chunker import (
    CHUNKER_REGISTRY,
    FixedSizeChunker,
    MedicalSectionChunker,
    RecursiveChunker,
    SemanticChunker,
    SentenceChunker,
    create_chunker,
)
from app.document_pipeline.cleaner import DefaultDocumentCleaner
from app.document_pipeline.config import DocumentPipelineConfig
from app.document_pipeline.document import ProcessedDocument, SectionInfo
from app.document_pipeline.exceptions import (
    ChunkingError,
    ClassificationError,
    DocumentCleanError,
    DocumentPipelineError,
    EmptyDocumentError,
    MalformedDocumentError,
    MetadataExtractionError,
    PipelineConfigurationError,
    SectionDetectionError,
    StageExecutionError,
    VersionTrackingError,
)
from app.document_pipeline.interfaces import (
    Chunker,
    DocumentCleaner,
    DocumentClassifier,
    MetadataExtractor,
    SectionDetector,
    VersionTracker,
)
from app.document_pipeline.metadata import DefaultMetadataExtractor
from app.document_pipeline.pipeline import (
    DocumentPipeline,
    SimpleDocumentClassifier,
    SimpleSectionDetector,
)
from app.document_pipeline.versioning import (
    DefaultVersionTracker,
    VersionInfo,
)

__all__ = [
    "DocumentPipeline",
    "DocumentPipelineConfig",
    "ProcessedDocument",
    "SectionInfo",
    "DocumentChunk",
    "ChunkMetadata",
    "DocumentCleaner",
    "DefaultDocumentCleaner",
    "DocumentClassifier",
    "SimpleDocumentClassifier",
    "SectionDetector",
    "SimpleSectionDetector",
    "Chunker",
    "FixedSizeChunker",
    "RecursiveChunker",
    "SemanticChunker",
    "MedicalSectionChunker",
    "SentenceChunker",
    "CHUNKER_REGISTRY",
    "create_chunker",
    "MetadataExtractor",
    "DefaultMetadataExtractor",
    "VersionTracker",
    "DefaultVersionTracker",
    "VersionInfo",
    "DocumentPipelineError",
    "PipelineConfigurationError",
    "DocumentCleanError",
    "ChunkingError",
    "MetadataExtractionError",
    "SectionDetectionError",
    "EmptyDocumentError",
    "MalformedDocumentError",
    "VersionTrackingError",
    "ClassificationError",
    "StageExecutionError",
]
