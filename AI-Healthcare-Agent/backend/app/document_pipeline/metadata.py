from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.document_pipeline.chunk import ChunkMetadata, DocumentChunk
from app.document_pipeline.document import ProcessedDocument
from app.document_pipeline.interfaces import MetadataExtractor
from app.document_pipeline.versioning import DefaultVersionTracker


class DefaultMetadataExtractor(MetadataExtractor):
    """Enriches each chunk with metadata from the processed document.

    Adds document-level fields (patient_id, report_id, document_type, language, source)
    and chunk-level fields (section, page, chunk_index, versions).
    """

    def __init__(self, version_tracker: Optional[DefaultVersionTracker] = None) -> None:
        self._version_tracker = version_tracker or DefaultVersionTracker()

    def extract(self, document: ProcessedDocument, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        if not chunks:
            return chunks

        enriched: list[DocumentChunk] = []
        for i, chunk in enumerate(chunks):
            section = self._find_section_for_chunk(document, chunk)

            meta = ChunkMetadata(
                document_id=document.report_id or "",
                patient_id=document.patient_id,
                report_id=document.report_id,
                document_type=document.document_type,
                section=section,
                page=chunk.metadata.page,
                chunk_index=i,
                chunk_version=self._version_tracker.get_document_version(),
                schema_version=self._version_tracker.get_schema_version(),
                embedding_version=self._version_tracker.get_embedding_version(),
                created_at=datetime.utcnow(),
                provider=document.provider,
                language=document.language,
                source=document.source,
                chunker_type=chunk.metadata.chunker_type,
            )

            enriched_chunk = DocumentChunk(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                text=chunk.text,
                metadata=meta,
            )
            enriched.append(enriched_chunk)

        return enriched

    def _find_section_for_chunk(self, document: ProcessedDocument, chunk: DocumentChunk) -> Optional[str]:
        if not document.sections:
            return None

        best_section: Optional[str] = None
        best_overlap = 0

        for sec in document.sections:
            if not sec.text:
                continue
            overlap = self._compute_overlap(chunk.text, sec.text)
            if overlap > best_overlap:
                best_overlap = overlap
                best_section = sec.header

        return best_section

    def _compute_overlap(self, text_a: str, text_b: str) -> int:
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        if not words_a or not words_b:
            return 0
        return len(words_a & words_b)
