from __future__ import annotations

import re
from typing import Optional

from app.document_pipeline.chunk import ChunkMetadata, DocumentChunk
from app.document_pipeline.config import DocumentPipelineConfig
from app.document_pipeline.document import ProcessedDocument
from app.document_pipeline.exceptions import ChunkingError
from app.document_pipeline.interfaces import Chunker

MEDICAL_SECTION_PATTERNS: dict[str, re.Pattern] = {
    "patient_information": re.compile(
        r"(?i)(?:patient\s*(?:name|information|details)|name\s*:)", re.MULTILINE
    ),
    "diagnosis": re.compile(
        r"(?i)(?:diagnosis|diagnoses|impression|assessment|clinical\s*impression)",
        re.MULTILINE,
    ),
    "medications": re.compile(
        r"(?i)(?:medications?|prescriptions?|drugs?|medicine|pharmacy|RX)",
        re.MULTILINE,
    ),
    "lab_results": re.compile(
        r"(?i)(?:lab\s*(?:results?|test|data)|laboratory|test\s*results?|investigations?)",
        re.MULTILINE,
    ),
    "doctor_notes": re.compile(
        r"(?i)(?:doctor'?s?\s*notes?|clinical\s*notes?|progress\s*notes?|physician\s*notes?)",
        re.MULTILINE,
    ),
    "follow_up": re.compile(
        r"(?i)(?:follow[- ]?up|followup|next\s*visit|return\s*visit|review)",
        re.MULTILINE,
    ),
    "vitals": re.compile(
        r"(?i)(?:vitals?|vital\s*signs?|bp|blood\s*pressure|heart\s*rate|temperature|pulse|oxygen)",
        re.MULTILINE,
    ),
    "prescriptions": re.compile(
        r"(?i)(?:prescriptions?|dispense|take|dosage|sig|directions?\s*for\s*use)",
        re.MULTILINE,
    ),
}


class FixedSizeChunker(Chunker):
    """Splits text into chunks of fixed character length with overlap."""

    def chunk(self, document: ProcessedDocument, config: DocumentPipelineConfig) -> list[DocumentChunk]:
        text = document.cleaned_text or document.raw_text
        if not text.strip():
            return []

        size = config.chunk_size
        overlap = config.chunk_overlap
        chunks: list[DocumentChunk] = []

        start = 0
        index = 0
        while start < len(text):
            end = min(start + size, len(text))
            if end < len(text):
                end = self._find_break(text, end)
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(self._make_chunk(document, chunk_text, index, config.chunker_type))
                index += 1
            start = end - overlap if end < len(text) else len(text)

        return chunks

    def _find_break(self, text: str, position: int) -> int:
        search_start = max(position - 50, 0)
        search_zone = text[search_start:position + 50]

        newline = search_zone.rfind("\n")
        if newline != -1:
            return search_start + newline + 1

        period = search_zone.rfind(". ")
        if period != -1:
            return search_start + period + 2

        space = search_zone.rfind(" ")
        if space != -1:
            return search_start + space + 1

        return position

    def _make_chunk(self, document: ProcessedDocument, text: str, index: int, chunker_type: str) -> DocumentChunk:
        return DocumentChunk(
            chunk_id=f"{document.report_id or 'doc'}_chunk_{index}",
            document_id=document.report_id or "",
            text=text,
            metadata=ChunkMetadata(
                chunk_index=index,
                report_id=document.report_id,
                patient_id=document.patient_id,
                document_type=document.document_type,
                page=self._estimate_page(document, text),
                source=document.source,
                language=document.language,
                provider=document.provider,
                chunker_type=chunker_type,
            ),
        )

    def _estimate_page(self, document: ProcessedDocument, text: str) -> Optional[int]:
        if document.page_count <= 1:
            return None
        total_len = len(document.cleaned_text or document.raw_text)
        if total_len == 0:
            return None
        char_pos = (document.cleaned_text or document.raw_text).find(text)
        if char_pos < 0:
            return None
        estimated_page = (char_pos / total_len) * document.page_count
        return int(estimated_page) + 1


class RecursiveChunker(Chunker):
    """Recursively splits text by natural boundaries: paragraphs, sentences, then fixed size."""

    def chunk(self, document: ProcessedDocument, config: DocumentPipelineConfig) -> list[DocumentChunk]:
        text = document.cleaned_text or document.raw_text
        if not text.strip():
            return []

        size = config.chunk_size
        overlap = config.chunk_overlap
        chunks: list[DocumentChunk] = []
        index = 0

        paragraphs = self._split_paragraphs(text)
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) <= size:
                current_chunk = (current_chunk + "\n\n" + para).strip()
            else:
                if current_chunk:
                    chunks.append(self._make_chunk(document, current_chunk, index, config.chunker_type))
                    index += 1
                    current_chunk = self._apply_overlap(current_chunk, para, overlap)
                else:
                    for sentence in self._split_sentences(para):
                        if len(current_chunk) + len(sentence) <= size:
                            current_chunk = (current_chunk + " " + sentence).strip()
                        else:
                            if current_chunk:
                                chunks.append(self._make_chunk(document, current_chunk, index, config.chunker_type))
                                index += 1
                            current_chunk = sentence

        if current_chunk:
            chunks.append(self._make_chunk(document, current_chunk, index, config.chunker_type))

        return chunks

    def _split_paragraphs(self, text: str) -> list[str]:
        raw = re.split(r"\n\s*\n", text)
        return [p.strip() for p in raw if p.strip()]

    def _split_sentences(self, text: str) -> list[str]:
        raw = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in raw if s.strip()]

    def _apply_overlap(self, current: str, next_para: str, overlap: int) -> str:
        words = (current + " " + next_para).split()
        if len(words) <= overlap:
            return current
        return " ".join(words[-overlap:])

    def _make_chunk(self, document: ProcessedDocument, text: str, index: int, chunker_type: str) -> DocumentChunk:
        return FixedSizeChunker()._make_chunk(document, text, index, chunker_type)


class SemanticChunker(Chunker):
    """Interface-only semantic chunker.

    Semantic chunking requires an embedding model to measure semantic similarity
    between sentences. This implementation provides a simple fixed-size fallback
    with a placeholder for future semantic splitting.
    """

    def chunk(self, document: ProcessedDocument, config: DocumentPipelineConfig) -> list[DocumentChunk]:
        return RecursiveChunker().chunk(document, config)


class MedicalSectionChunker(Chunker):
    """Splits document by detected medical sections.

    Each medical section becomes one or more chunks depending on section length.
    Sections not matching known patterns are grouped into a 'general' section.
    """

    def __init__(self, section_patterns: Optional[dict[str, re.Pattern]] = None) -> None:
        self._patterns = section_patterns or MEDICAL_SECTION_PATTERNS

    def chunk(self, document: ProcessedDocument, config: DocumentPipelineConfig) -> list[DocumentChunk]:
        text = document.cleaned_text or document.raw_text
        if not text.strip():
            return []

        if document.sections:
            return self._chunk_by_detected_sections(document, config)

        return self._chunk_by_pattern_matching(document, config, text)

    def _chunk_by_detected_sections(self, document: ProcessedDocument, config: DocumentPipelineConfig) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        index = 0
        for sec in document.sections:
            if not sec.text.strip():
                continue
            sec_chunks = self._split_long_section(
                document, sec.text, sec.header, index, config
            )
            chunks.extend(sec_chunks)
            index += len(sec_chunks)
        return chunks

    def _chunk_by_pattern_matching(self, document: ProcessedDocument, config: DocumentPipelineConfig, text: str) -> list[DocumentChunk]:
        sections = self._detect_sections(text)
        chunks: list[DocumentChunk] = []
        index = 0

        for header, content in sections.items():
            if not content.strip():
                continue
            sec_chunks = self._split_long_section(
                document, content, header, index, config
            )
            chunks.extend(sec_chunks)
            index += len(sec_chunks)

        return chunks

    def _detect_sections(self, text: str) -> dict[str, str]:
        lines = text.split("\n")
        sections: dict[str, str] = {}
        current_section = "general"
        current_lines: list[str] = []

        for line in lines:
            matched = False
            for header, pattern in self._patterns.items():
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

    def _split_long_section(self, document: ProcessedDocument, text: str, header: str, index: int, config: DocumentPipelineConfig) -> list[DocumentChunk]:
        if len(text) <= config.chunk_size:
            chunk = FixedSizeChunker()._make_chunk(document, text, index, config.chunker_type)
            chunk.metadata.section = header
            return [chunk]

        chunks: list[DocumentChunk] = []
        fixed = FixedSizeChunker()
        temp_doc = document.model_copy(deep=True)
        temp_doc.cleaned_text = text
        fixed_chunks = fixed.chunk(temp_doc, config)
        for i, fc in enumerate(fixed_chunks):
            fc.metadata.section = header
            fc.metadata.chunk_index = index + i
            chunks.append(fc)
        return chunks


class SentenceChunker(Chunker):
    """Splits text by sentence boundaries, grouping until chunk_size is reached."""

    def chunk(self, document: ProcessedDocument, config: DocumentPipelineConfig) -> list[DocumentChunk]:
        text = document.cleaned_text or document.raw_text
        if not text.strip():
            return []

        sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks: list[DocumentChunk] = []
        current_chunk = ""
        index = 0

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= config.chunk_size:
                current_chunk = (current_chunk + " " + sentence).strip()
            else:
                if current_chunk:
                    chunks.append(self._make_chunk(document, current_chunk, index, config.chunker_type))
                    index += 1
                current_chunk = sentence

        if current_chunk:
            chunks.append(self._make_chunk(document, current_chunk, index, config.chunker_type))

        return chunks

    def _make_chunk(self, document: ProcessedDocument, text: str, index: int, chunker_type: str) -> DocumentChunk:
        return FixedSizeChunker()._make_chunk(document, text, index, chunker_type)


CHUNKER_REGISTRY: dict[str, type[Chunker]] = {
    "fixed": FixedSizeChunker,
    "recursive": RecursiveChunker,
    "semantic": SemanticChunker,
    "medical_section": MedicalSectionChunker,
    "sentence": SentenceChunker,
}


def create_chunker(chunker_type: str) -> Chunker:
    if chunker_type not in CHUNKER_REGISTRY:
        raise ChunkingError(
            f"Unknown chunker type '{chunker_type}'. "
            f"Available: {list(CHUNKER_REGISTRY.keys())}"
        )
    return CHUNKER_REGISTRY[chunker_type]()
