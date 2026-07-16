from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from app.document_pipeline.chunk import DocumentChunk
from app.document_pipeline.cleaner import DefaultDocumentCleaner
from app.document_pipeline.config import DocumentPipelineConfig
from app.document_pipeline.document import ProcessedDocument, SectionInfo
from app.document_pipeline.exceptions import (
    DocumentPipelineError,
    EmptyDocumentError,
    MalformedDocumentError,
    StageExecutionError,
)
from app.document_pipeline.interfaces import (
    Chunker,
    DocumentCleaner,
    DocumentClassifier,
    MetadataExtractor,
    SectionDetector,
)
from app.document_pipeline.metadata import DefaultMetadataExtractor
from app.document_pipeline.versioning import DefaultVersionTracker
from app.document_pipeline.chunker import (
    MEDICAL_SECTION_PATTERNS,
    Chunker as DefaultChunker,
    create_chunker,
)


class SimpleSectionDetector(SectionDetector):
    """Detects medical sections using regex patterns."""

    def __init__(self, patterns: Optional[dict[str, str]] = None) -> None:
        self._patterns = patterns or {
            name: pattern.pattern
            for name, pattern in MEDICAL_SECTION_PATTERNS.items()
        }
        self._compiled = {
            name: __import__("re").compile(pat)
            for name, pat in self._patterns.items()
        }

    def detect_sections(self, text: str) -> dict[str, str]:
        import re

        lines = text.split("\n")
        sections: dict[str, str] = {}
        current_section = "general"
        current_lines: list[str] = []

        for line in lines:
            matched = False
            for header, pattern in self._compiled.items():
                if pattern.search(line):
                    if current_lines:
                        sections[current_section] = "\n".join(current_lines).strip()
                    current_section = header
                    current_lines = [line]
                    matched = True
                    break
            if not matched:
                current_lines.append(line)

        if current_lines:
            sections[current_section] = "\n".join(current_lines).strip()

        return sections


class SimpleDocumentClassifier(DocumentClassifier):
    """Classifies documents using keyword scoring."""

    CLASSIFICATION_RULES: dict[str, list[str]] = {
        "prescription": [
            "prescription", "rx", "medication", "dosage", "take",
            "sig", "dispense", "tablet", "capsule", "mg",
        ],
        "lab_report": [
            "lab", "laboratory", "test result", "value", "reference range",
            "specimen", "collected", "reported", "hgba1c", "glucose",
        ],
        "discharge_summary": [
            "discharge", "admission", "hospital course", "discharge diagnosis",
            "discharge medication", "follow-up instructions",
        ],
        "radiology_report": [
            "radiology", "x-ray", "xray", "mri", "ct scan", "ultrasound",
            "radiologist", "findings", "impression",
        ],
        "consultation": [
            "consultation", "referred", "specialist", "opinion",
            "history of present illness", "assessment and plan",
        ],
    }

    def classify(self, text: str) -> str:
        if not text.strip():
            return "unknown"

        text_lower = text.lower()
        scores: dict[str, int] = {}

        for doc_type, keywords in self.CLASSIFICATION_RULES.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[doc_type] = score

        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return "unknown"

        return best


class DocumentPipeline:
    """Orchestrates the document processing pipeline.

    Flow:
        Input → Clean → Classify → Detect Sections → Chunk → Enrich Metadata → Output
    """

    def __init__(
        self,
        config: Optional[DocumentPipelineConfig] = None,
        cleaner: Optional[DocumentCleaner] = None,
        classifier: Optional[DocumentClassifier] = None,
        section_detector: Optional[SectionDetector] = None,
        chunker: Optional[Chunker] = None,
        metadata_extractor: Optional[MetadataExtractor] = None,
        version_tracker: Optional[DefaultVersionTracker] = None,
    ) -> None:
        self.config = config or DocumentPipelineConfig()
        self.cleaner = cleaner or DefaultDocumentCleaner()
        self.classifier = classifier or SimpleDocumentClassifier()
        self.section_detector = section_detector or SimpleSectionDetector()
        self.chunker = chunker or create_chunker(self.config.chunker_type)
        self.metadata_extractor = metadata_extractor or DefaultMetadataExtractor(
            version_tracker=version_tracker or DefaultVersionTracker()
        )
        self._version_tracker = version_tracker or DefaultVersionTracker()

    def process(
        self,
        raw_text: str,
        patient_id: Optional[str] = None,
        report_id: Optional[str] = None,
        source: str = "ocr",
        language: str = "en",
        provider: str = "unknown",
        page_count: int = 1,
    ) -> list[DocumentChunk]:
        """Run the full pipeline on raw OCR text and return enriched chunks."""

        if not raw_text or not raw_text.strip():
            raise MalformedDocumentError("Input text is empty or whitespace only")

        document_id = report_id or str(uuid.uuid4())

        try:
            cleaned = self._stage_clean(raw_text)
            doc_type = self._stage_classify(cleaned)
            sections_raw = self._stage_detect_sections(cleaned)
            sections = self._build_section_objects(sections_raw)
            document = self._build_document(
                raw_text, cleaned, doc_type, sections,
                patient_id, report_id, source, language, provider, page_count,
            )
            chunks = self._stage_chunk(document)
            enriched = self._stage_enrich(document, chunks)
            self._finalize_chunks(enriched, document_id, report_id)
            return enriched

        except DocumentPipelineError:
            raise
        except Exception as exc:
            raise StageExecutionError(f"Pipeline execution failed: {exc}") from exc

    def _stage_clean(self, raw_text: str) -> str:
        return self.cleaner.clean(raw_text, self.config)

    def _stage_classify(self, text: str) -> str:
        if not self.config.enable_classification:
            return "unknown"
        return self.classifier.classify(text)

    def _stage_detect_sections(self, text: str) -> dict[str, str]:
        return self.section_detector.detect_sections(text)

    def _stage_chunk(self, document: ProcessedDocument) -> list[DocumentChunk]:
        if not document.cleaned_text.strip():
            raise EmptyDocumentError("Cannot chunk an empty document")
        return self.chunker.chunk(document, self.config)

    def _stage_enrich(self, document: ProcessedDocument, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        if not self.config.enable_metadata:
            return chunks
        return self.metadata_extractor.extract(document, chunks)

    def _build_section_objects(self, sections_raw: dict[str, str]) -> list[SectionInfo]:
        return [
            SectionInfo(header=header, text=text, index=i)
            for i, (header, text) in enumerate(sections_raw.items())
        ]

    def _build_document(
        self,
        raw_text: str,
        cleaned_text: str,
        doc_type: str,
        sections: list[SectionInfo],
        patient_id: Optional[str],
        report_id: Optional[str],
        source: str,
        language: str,
        provider: str,
        page_count: int,
    ) -> ProcessedDocument:
        return ProcessedDocument(
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            document_type=doc_type,
            sections=sections,
            patient_id=patient_id,
            report_id=report_id,
            source=source,
            language=language,
            provider=provider,
            page_count=page_count,
            created_at=datetime.utcnow(),
        )

    def _finalize_chunks(
        self,
        chunks: list[DocumentChunk],
        document_id: str,
        report_id: Optional[str],
    ) -> None:
        for chunk in chunks:
            chunk.document_id = document_id
            chunk.metadata.document_id = document_id
            if report_id:
                chunk.metadata.report_id = report_id
            if not chunk.chunk_id:
                chunk.chunk_id = f"{document_id}_chunk_{chunk.metadata.chunk_index}"
