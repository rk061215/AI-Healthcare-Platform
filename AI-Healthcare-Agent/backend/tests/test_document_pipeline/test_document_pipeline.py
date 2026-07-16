from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest

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
    DocumentCleanError,
    DocumentPipelineError,
    EmptyDocumentError,
    MalformedDocumentError,
    PipelineConfigurationError,
)
from app.document_pipeline.metadata import DefaultMetadataExtractor
from app.document_pipeline.pipeline import (
    DocumentPipeline,
    SimpleDocumentClassifier,
    SimpleSectionDetector,
)
from app.document_pipeline.versioning import DefaultVersionTracker, VersionInfo

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_ocr_text() -> str:
    return """
Patient Name: John Doe
DOB: 1990-05-20
Date: 2026-01-15
Dr. Sarah Smith
General Hospital

Diagnosis: Type 2 Diabetes Mellitus

Medications:
Metformin 500mg twice daily with meals
Lisinopril 10mg once daily

Lab Results:
Blood Glucose 126 mg/dL
HbA1c 7.2 %

Follow-up: 2026-04-15
Notes: Monitor blood sugar levels
"""


@pytest.fixture
def multi_page_text() -> str:
    return """
Patient Name: Jane Smith
DOB: 1985-08-12
Date: 2026-03-01
Dr. Robert Brown
City Medical Center

Diagnosis: Asthma, Allergic Rhinitis

Medications:
Albuterol 90mcg 2 puffs as needed for wheezing
Fluticasone 250mcg once daily

--- Page 2 ---

Lab Results:
IgE 250 IU/mL
Eosinophil count 0.5 10^9/L

Follow-up: 2026-06-01
Notes: Avoid known triggers. Use peak flow meter daily.
"""


@pytest.fixture
def config() -> DocumentPipelineConfig:
    return DocumentPipelineConfig(chunker_type="recursive", chunk_size=200, chunk_overlap=20)


@pytest.fixture
def pipeline(config: DocumentPipelineConfig) -> DocumentPipeline:
    return DocumentPipeline(config=config)


@pytest.fixture
def processed_doc(sample_ocr_text: str) -> ProcessedDocument:
    cleaner = DefaultDocumentCleaner()
    cleaned = cleaner.clean(sample_ocr_text)
    return ProcessedDocument(
        raw_text=sample_ocr_text,
        cleaned_text=cleaned,
        document_type="prescription",
        sections=[
            SectionInfo(header="diagnosis", text="Diagnosis: Type 2 Diabetes Mellitus", index=0),
            SectionInfo(header="medications", text="Metformin 500mg twice daily with meals\nLisinopril 10mg once daily", index=1),
            SectionInfo(header="lab_results", text="Blood Glucose 126 mg/dL\nHbA1c 7.2 %", index=2),
        ],
        patient_id="pat_001",
        report_id="rep_001",
        source="ocr",
        language="en",
        provider="google_vision",
        page_count=1,
    )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


class TestDocumentPipelineConfig:
    def test_default_config(self) -> None:
        cfg = DocumentPipelineConfig()
        assert cfg.chunker_type == "recursive"
        assert cfg.chunk_size == 500
        assert cfg.chunk_overlap == 50

    def test_valid_chunker_types(self) -> None:
        for t in ["fixed", "recursive", "semantic", "medical_section", "sentence"]:
            cfg = DocumentPipelineConfig(chunker_type=t)
            assert cfg.chunker_type == t

    def test_invalid_chunker_type_raises(self) -> None:
        with pytest.raises(PipelineConfigurationError, match="Invalid chunker_type"):
            DocumentPipelineConfig(chunker_type="invalid")

    def test_chunk_size_validation(self) -> None:
        with pytest.raises(PipelineConfigurationError, match="chunk_size"):
            DocumentPipelineConfig(chunk_size=10, min_chunk_size=50)

    def test_chunk_overlap_validation(self) -> None:
        with pytest.raises(PipelineConfigurationError, match="chunk_overlap"):
            DocumentPipelineConfig(chunk_size=100, chunk_overlap=100)

    def test_max_chunk_size_validation(self) -> None:
        with pytest.raises(PipelineConfigurationError, match="chunk_size"):
            DocumentPipelineConfig(chunk_size=5000, max_chunk_size=2000)


# ---------------------------------------------------------------------------
# Cleaner
# ---------------------------------------------------------------------------


class TestDefaultDocumentCleaner:
    def test_clean_removes_null_bytes(self) -> None:
        cleaner = DefaultDocumentCleaner()
        result = cleaner.clean("Hello\x00 World")
        assert "\x00" not in result

    def test_clean_normalizes_newlines(self) -> None:
        cleaner = DefaultDocumentCleaner()
        result = cleaner.clean("Line1\r\nLine2\rLine3\n\n\nLine4")
        assert result == "Line1\nLine2\nLine3\n\nLine4"

    def test_clean_collapses_whitespace(self) -> None:
        cleaner = DefaultDocumentCleaner()
        result = cleaner.clean("Hello    World   Test")
        assert "Hello World Test" in result

    def test_clean_strips_page_separators(self) -> None:
        cleaner = DefaultDocumentCleaner()
        result = cleaner.clean("Text before\n--- Page 2 ---\nText after")
        assert "--- Page 2 ---" not in result
        assert "Text before" in result
        assert "Text after" in result

    def test_clean_removes_non_breaking_spaces(self) -> None:
        cleaner = DefaultDocumentCleaner()
        result = cleaner.clean("Hello\xa0World")
        assert "\xa0" not in result

    def test_clean_empty_text_raises(self) -> None:
        cleaner = DefaultDocumentCleaner()
        with pytest.raises(EmptyDocumentError):
            cleaner.clean("")

    def test_clean_whitespace_only_raises(self) -> None:
        cleaner = DefaultDocumentCleaner()
        with pytest.raises(EmptyDocumentError):
            cleaner.clean("   \n  \n  ")

    def test_clean_respects_max_length(self) -> None:
        cleaner = DefaultDocumentCleaner()
        cfg = DocumentPipelineConfig(max_document_length=10)
        result = cleaner.clean("Hello World! This is a long document.", cfg)
        assert len(result) <= 10

    def test_clean_preserves_meaningful_content(self) -> None:
        cleaner = DefaultDocumentCleaner()
        text = "Patient Name: John Doe\nDiagnosis: Hypertension"
        result = cleaner.clean(text)
        assert "Patient Name: John Doe" in result
        assert "Diagnosis: Hypertension" in result


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


class TestFixedSizeChunker:
    def test_chunk_creates_multiple_chunks(self, processed_doc: ProcessedDocument) -> None:
        chunker = FixedSizeChunker()
        config = DocumentPipelineConfig(chunker_type="fixed", chunk_size=100, chunk_overlap=10)
        chunks = chunker.chunk(processed_doc, config)
        assert len(chunks) > 1

    def test_chunk_preserves_text(self, processed_doc: ProcessedDocument) -> None:
        chunker = FixedSizeChunker()
        config = DocumentPipelineConfig(chunker_type="fixed", chunk_size=500, chunk_overlap=50)
        chunks = chunker.chunk(processed_doc, config)
        combined = " ".join(c.text for c in chunks)
        assert "Diagnosis" in combined
        assert "Metformin" in combined

    def test_chunk_empty_document(self) -> None:
        chunker = FixedSizeChunker()
        doc = ProcessedDocument(raw_text="", cleaned_text="")
        config = DocumentPipelineConfig(chunker_type="fixed")
        chunks = chunker.chunk(doc, config)
        assert chunks == []

    def test_chunk_index_increments(self, processed_doc: ProcessedDocument) -> None:
        chunker = FixedSizeChunker()
        config = DocumentPipelineConfig(chunker_type="fixed", chunk_size=50, chunk_overlap=10)
        chunks = chunker.chunk(processed_doc, config)
        for i, c in enumerate(chunks):
            assert c.metadata.chunk_index == i

    def test_chunk_document_id(self, processed_doc: ProcessedDocument) -> None:
        chunker = FixedSizeChunker()
        config = DocumentPipelineConfig(chunker_type="fixed", chunk_size=500)
        chunks = chunker.chunk(processed_doc, config)
        for c in chunks:
            assert c.document_id == processed_doc.report_id or ""


class TestRecursiveChunker:
    def test_chunk_by_paragraphs(self, processed_doc: ProcessedDocument) -> None:
        chunker = RecursiveChunker()
        config = DocumentPipelineConfig(chunker_type="recursive", chunk_size=200, chunk_overlap=20)
        chunks = chunker.chunk(processed_doc, config)
        assert len(chunks) >= 1
        combined = " ".join(c.text for c in chunks)
        assert "Metformin" in combined

    def test_chunk_preserves_sentence_boundaries(self) -> None:
        text = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        doc = ProcessedDocument(raw_text=text, cleaned_text=text)
        chunker = RecursiveChunker()
        config = DocumentPipelineConfig(chunker_type="recursive", chunk_size=50, chunk_overlap=10)
        chunks = chunker.chunk(doc, config)
        assert len(chunks) >= 1

    def test_chunk_empty(self) -> None:
        chunker = RecursiveChunker()
        doc = ProcessedDocument(raw_text="", cleaned_text="")
        config = DocumentPipelineConfig(chunker_type="recursive")
        assert chunker.chunk(doc, config) == []


class TestMedicalSectionChunker:
    def test_detects_medical_sections(self, sample_ocr_text: str) -> None:
        chunker = MedicalSectionChunker()
        cleaner = DefaultDocumentCleaner()
        cleaned = cleaner.clean(sample_ocr_text)
        doc = ProcessedDocument(raw_text=sample_ocr_text, cleaned_text=cleaned, document_type="prescription")
        config = DocumentPipelineConfig(chunker_type="medical_section", chunk_size=500)
        chunks = chunker.chunk(doc, config)
        sections_found = {c.metadata.section for c in chunks if c.metadata.section}
        assert "diagnosis" in sections_found or "medications" in sections_found or "lab_results" in sections_found

    def test_uses_existing_sections(self, processed_doc: ProcessedDocument) -> None:
        chunker = MedicalSectionChunker()
        config = DocumentPipelineConfig(chunker_type="medical_section", chunk_size=500)
        chunks = chunker.chunk(processed_doc, config)
        sections_found = {c.metadata.section for c in chunks if c.metadata.section}
        assert "diagnosis" in sections_found

    def test_sections_appear_as_separate_chunks(self) -> None:
        text = """
Patient Name: John Doe

Diagnosis: Hypertension. Patient has elevated blood pressure.

Medications: Lisinopril 10mg once daily for blood pressure control.

Lab Results: Blood Glucose 95 mg/dL within normal range.
"""
        cleaner = DefaultDocumentCleaner()
        cleaned = cleaner.clean(text)
        doc = ProcessedDocument(raw_text=text, cleaned_text=cleaned)
        chunker = MedicalSectionChunker()
        config = DocumentPipelineConfig(chunker_type="medical_section", chunk_size=500)
        chunks = chunker.chunk(doc, config)
        sections = [c.metadata.section for c in chunks]
        assert any(s for s in sections if s)  # at least one section found


class TestSentenceChunker:
    def test_chunks_by_sentence(self) -> None:
        text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here."
        doc = ProcessedDocument(raw_text=text, cleaned_text=text)
        chunker = SentenceChunker()
        config = DocumentPipelineConfig(chunker_type="sentence", chunk_size=100, chunk_overlap=0)
        chunks = chunker.chunk(doc, config)
        assert len(chunks) >= 1

    def test_empty_document(self) -> None:
        chunker = SentenceChunker()
        doc = ProcessedDocument(raw_text="", cleaned_text="")
        config = DocumentPipelineConfig(chunker_type="sentence")
        assert chunker.chunk(doc, config) == []


class TestSemanticChunker:
    def test_falls_back_to_recursive(self, processed_doc: ProcessedDocument) -> None:
        chunker = SemanticChunker()
        config = DocumentPipelineConfig(chunker_type="semantic", chunk_size=200, chunk_overlap=20)
        chunks = chunker.chunk(processed_doc, config)
        assert len(chunks) >= 1

    def test_empty_document(self) -> None:
        chunker = SemanticChunker()
        doc = ProcessedDocument(raw_text="", cleaned_text="")
        config = DocumentPipelineConfig(chunker_type="semantic")
        assert chunker.chunk(doc, config) == []


class TestChunkerRegistry:
    def test_all_types_registered(self) -> None:
        for t in ["fixed", "recursive", "semantic", "medical_section", "sentence"]:
            assert t in CHUNKER_REGISTRY

    def test_create_chunker(self) -> None:
        chunker = create_chunker("fixed")
        assert isinstance(chunker, FixedSizeChunker)

    def test_create_unknown_raises(self) -> None:
        with pytest.raises(ChunkingError, match="Unknown chunker type"):
            create_chunker("nonexistent")


# ---------------------------------------------------------------------------
# Section Detection
# ---------------------------------------------------------------------------


class TestSimpleSectionDetector:
    def test_detects_diagnosis_section(self, sample_ocr_text: str) -> None:
        detector = SimpleSectionDetector()
        sections = detector.detect_sections(sample_ocr_text)
        assert "diagnosis" in sections

    def test_detects_medications_section(self, sample_ocr_text: str) -> None:
        detector = SimpleSectionDetector()
        sections = detector.detect_sections(sample_ocr_text)
        assert "medications" in sections

    def test_detects_lab_results_section(self, sample_ocr_text: str) -> None:
        detector = SimpleSectionDetector()
        sections = detector.detect_sections(sample_ocr_text)
        assert "lab_results" in sections

    def test_returns_general_for_plain_text(self) -> None:
        detector = SimpleSectionDetector()
        sections = detector.detect_sections("Some plain text without medical sections.")
        assert "general" in sections

    def test_empty_text_returns_general(self) -> None:
        detector = SimpleSectionDetector()
        sections = detector.detect_sections("")
        assert "general" in sections or sections == {}


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------


class TestSimpleDocumentClassifier:
    def test_classifies_prescription(self) -> None:
        classifier = SimpleDocumentClassifier()
        result = classifier.classify("Take Metformin 500mg twice daily")
        assert result == "prescription"

    def test_classifies_lab_report(self) -> None:
        classifier = SimpleDocumentClassifier()
        result = classifier.classify("Laboratory Results\nGlucose: 126 mg/dL\nHbA1c: 7.2%\nSpecimen: Blood")
        assert result == "lab_report"

    def test_classifies_discharge_summary(self) -> None:
        classifier = SimpleDocumentClassifier()
        result = classifier.classify("Discharge Diagnosis: Hypertension\nFollow-up instructions")
        assert result == "discharge_summary"

    def test_classifies_radiology(self) -> None:
        classifier = SimpleDocumentClassifier()
        result = classifier.classify("MRI findings show no abnormalities")
        assert result == "radiology_report"

    def test_classifies_consultation(self) -> None:
        classifier = SimpleDocumentClassifier()
        result = classifier.classify("Consultation: Referred to cardiology")
        assert result == "consultation"

    def test_classifies_unknown(self) -> None:
        classifier = SimpleDocumentClassifier()
        result = classifier.classify("This is some random text")
        assert result == "unknown"

    def test_classifies_empty(self) -> None:
        classifier = SimpleDocumentClassifier()
        result = classifier.classify("")
        assert result == "unknown"


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class TestDefaultMetadataExtractor:
    def test_enriches_chunk_metadata(self, processed_doc: ProcessedDocument) -> None:
        chunk = DocumentChunk(chunk_id="chunk_0", document_id="rep_001", text="Test content")
        extractor = DefaultMetadataExtractor()
        enriched = extractor.extract(processed_doc, [chunk])
        assert len(enriched) == 1
        assert enriched[0].metadata.document_type == "prescription"
        assert enriched[0].metadata.patient_id == "pat_001"
        assert enriched[0].metadata.report_id == "rep_001"

    def test_empty_chunks_list(self, processed_doc: ProcessedDocument) -> None:
        extractor = DefaultMetadataExtractor()
        assert extractor.extract(processed_doc, []) == []

    def test_version_fields_populated(self, processed_doc: ProcessedDocument) -> None:
        chunk = DocumentChunk(chunk_id="chunk_0", document_id="rep_001", text="Test")
        tracker = DefaultVersionTracker(
            VersionInfo(document_version="2.0.0", schema_version="2.0.0", embedding_version="1.5.0")
        )
        extractor = DefaultMetadataExtractor(version_tracker=tracker)
        enriched = extractor.extract(processed_doc, [chunk])
        assert enriched[0].metadata.chunk_version == "2.0.0"
        assert enriched[0].metadata.schema_version == "2.0.0"
        assert enriched[0].metadata.embedding_version == "1.5.0"

    def test_section_assignment(self) -> None:
        doc = ProcessedDocument(
            raw_text="Diagnosis text",
            cleaned_text="Diagnosis text",
            document_type="prescription",
            sections=[
                SectionInfo(header="diagnosis", text="The diagnosis is hypertension", index=0),
            ],
        )
        chunk = DocumentChunk(chunk_id="chunk_0", document_id="doc_1", text="diagnosis is hypertension")
        extractor = DefaultMetadataExtractor()
        enriched = extractor.extract(doc, [chunk])
        assert enriched[0].metadata.section == "diagnosis"


# ---------------------------------------------------------------------------
# Version Tracking
# ---------------------------------------------------------------------------


class TestDefaultVersionTracker:
    def test_default_versions(self) -> None:
        tracker = DefaultVersionTracker()
        assert tracker.get_document_version() == "1.0.0"
        assert tracker.get_extraction_version() == "1.0.0"
        assert tracker.get_schema_version() == "1.0.0"

    def test_custom_versions(self) -> None:
        info = VersionInfo(document_version="2.0.0", extraction_version="1.5.0")
        tracker = DefaultVersionTracker(version_override=info)
        assert tracker.get_document_version() == "2.0.0"
        assert tracker.get_extraction_version() == "1.5.0"

    def test_embedding_version_empty_by_default(self) -> None:
        tracker = DefaultVersionTracker()
        assert tracker.get_embedding_version() == ""


class TestVersionInfo:
    def test_default_values(self) -> None:
        v = VersionInfo()
        assert v.document_version == "1.0.0"
        assert v.extraction_version == "1.0.0"
        assert v.schema_version == "1.0.0"

    def test_custom_values(self) -> None:
        v = VersionInfo(document_version="3.0.0", embedding_version="2.0.0")
        assert v.document_version == "3.0.0"
        assert v.embedding_version == "2.0.0"


# ---------------------------------------------------------------------------
# Pipeline Orchestration
# ---------------------------------------------------------------------------


class TestDocumentPipeline:
    def test_full_pipeline_returns_chunks(self, sample_ocr_text: str) -> None:
        pipeline = DocumentPipeline()
        chunks = pipeline.process(
            raw_text=sample_ocr_text,
            patient_id="pat_001",
            report_id="rep_001",
            provider="google_vision",
        )
        assert len(chunks) >= 1
        assert all(isinstance(c, DocumentChunk) for c in chunks)

    def test_pipeline_chunks_have_metadata(self, sample_ocr_text: str) -> None:
        pipeline = DocumentPipeline()
        chunks = pipeline.process(
            raw_text=sample_ocr_text,
            patient_id="pat_001",
            report_id="rep_001",
            provider="google_vision",
        )
        for c in chunks:
            assert c.metadata.document_id == "rep_001"
            assert c.metadata.patient_id == "pat_001"
            assert c.metadata.provider == "google_vision"

    def test_pipeline_with_config(self, sample_ocr_text: str) -> None:
        cfg = DocumentPipelineConfig(chunker_type="fixed", chunk_size=100, chunk_overlap=10)
        pipeline = DocumentPipeline(config=cfg)
        chunks = pipeline.process(raw_text=sample_ocr_text)
        assert len(chunks) > 1

    def test_pipeline_with_medical_section_chunker(self, sample_ocr_text: str) -> None:
        cfg = DocumentPipelineConfig(chunker_type="medical_section", chunk_size=500)
        pipeline = DocumentPipeline(config=cfg)
        chunks = pipeline.process(raw_text=sample_ocr_text)
        sections = {c.metadata.section for c in chunks if c.metadata.section}
        assert any(sections)  # at least one section was detected

    def test_pipeline_rejects_empty_input(self) -> None:
        pipeline = DocumentPipeline()
        with pytest.raises(MalformedDocumentError, match="empty"):
            pipeline.process(raw_text="")

    def test_pipeline_rejects_whitespace_only(self) -> None:
        pipeline = DocumentPipeline()
        with pytest.raises(MalformedDocumentError, match="empty"):
            pipeline.process(raw_text="   \n  \n  ")

    def test_pipeline_multi_page_document(self, multi_page_text: str) -> None:
        pipeline = DocumentPipeline()
        chunks = pipeline.process(
            raw_text=multi_page_text,
            report_id="rep_multi",
            page_count=2,
            provider="google_vision",
        )
        assert len(chunks) >= 1

    def test_pipeline_all_chunkers_produce_output(self, sample_ocr_text: str) -> None:
        for chunker_type in ["fixed", "recursive", "medical_section", "sentence"]:
            cfg = DocumentPipelineConfig(chunker_type=chunker_type, chunk_size=200, chunk_overlap=20)
            pipeline = DocumentPipeline(config=cfg)
            chunks = pipeline.process(raw_text=sample_ocr_text, report_id=f"rep_{chunker_type}")
            assert len(chunks) >= 1, f"Chunker '{chunker_type}' produced no output"

    def test_pipeline_classifier_runs(self, sample_ocr_text: str) -> None:
        pipeline = DocumentPipeline()
        chunks = pipeline.process(raw_text=sample_ocr_text, report_id="rep_classify")
        for c in chunks:
            assert c.metadata.document_type != ""

    def test_pipeline_with_classification_disabled(self, sample_ocr_text: str) -> None:
        cfg = DocumentPipelineConfig(enable_classification=False)
        pipeline = DocumentPipeline(config=cfg)
        chunks = pipeline.process(raw_text=sample_ocr_text, report_id="rep_noclass")
        for c in chunks:
            assert c.metadata.document_type == "unknown"

    def test_pipeline_with_metadata_disabled(self, sample_ocr_text: str) -> None:
        cfg = DocumentPipelineConfig(enable_metadata=False)
        pipeline = DocumentPipeline(config=cfg)
        chunks = pipeline.process(raw_text=sample_ocr_text, report_id="rep_nometa")
        for c in chunks:
            assert c.metadata.provider == "unknown"  # default, not enriched

    def test_pipeline_chunk_id_format(self, sample_ocr_text: str) -> None:
        pipeline = DocumentPipeline()
        chunks = pipeline.process(raw_text=sample_ocr_text, report_id="rep_id_001")
        for c in chunks:
            assert c.chunk_id.startswith("rep_id_001_chunk_")

    def test_pipeline_inject_components(self, sample_ocr_text: str) -> None:
        class UpperCaseCleaner:
            def clean(self, text: str, config=None) -> str:
                return text.upper().strip()

        pipeline = DocumentPipeline(cleaner=UpperCaseCleaner())  # type: ignore[arg-type]
        chunks = pipeline.process(raw_text=sample_ocr_text, report_id="rep_inject")
        assert len(chunks) >= 1

    def test_pipeline_dependency_injection_all_stages(self, sample_ocr_text: str) -> None:
        call_log: list[str] = []

        class LoggingCleaner:
            def clean(self, text: str, config=None) -> str:
                call_log.append("clean")
                return text.strip()

        class LoggingClassifier:
            def classify(self, text: str) -> str:
                call_log.append("classify")
                return "prescription"

        class LoggingDetector:
            def detect_sections(self, text: str) -> dict[str, str]:
                call_log.append("detect_sections")
                return {"general": text}

        pipeline = DocumentPipeline(
            cleaner=LoggingCleaner(),  # type: ignore[arg-type]
            classifier=LoggingClassifier(),  # type: ignore[arg-type]
            section_detector=LoggingDetector(),  # type: ignore[arg-type]
        )
        pipeline.process(raw_text=sample_ocr_text, report_id="rep_logs")
        assert "clean" in call_log
        assert "classify" in call_log
        assert "detect_sections" in call_log


# ---------------------------------------------------------------------------
# Error Handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    def test_malformed_input_raises(self) -> None:
        pipeline = DocumentPipeline()
        with pytest.raises(MalformedDocumentError):
            pipeline.process(raw_text="")

    def test_empty_after_clean_raises(self) -> None:
        cleaner = DefaultDocumentCleaner()
        with pytest.raises(EmptyDocumentError):
            cleaner.clean("")

    def test_pipeline_config_error(self) -> None:
        with pytest.raises(PipelineConfigurationError):
            DocumentPipelineConfig(chunker_type="bad")

    def test_unknown_chunker_raises(self) -> None:
        with pytest.raises(ChunkingError):
            create_chunker("unknown")

    def test_clean_error_propagation(self) -> None:
        class FailingCleaner:
            def clean(self, text: str, config=None) -> str:
                msg = "Cleaner failed"
                raise RuntimeError(msg)

        pipeline = DocumentPipeline(cleaner=FailingCleaner())  # type: ignore[arg-type]
        with pytest.raises(DocumentPipelineError):
            pipeline.process(raw_text="Some text")


# ---------------------------------------------------------------------------
# Document Model
# ---------------------------------------------------------------------------


class TestProcessedDocument:
    def test_default_field_values(self) -> None:
        doc = ProcessedDocument(raw_text="test")
        assert doc.document_type == "unknown"
        assert doc.sections == []
        assert doc.source == "ocr"
        assert doc.language == "en"

    def test_custom_fields(self) -> None:
        doc = ProcessedDocument(
            raw_text="test",
            cleaned_text="cleaned",
            document_type="prescription",
            patient_id="pat_001",
            report_id="rep_001",
        )
        assert doc.cleaned_text == "cleaned"
        assert doc.patient_id == "pat_001"

    def test_created_at_generated(self) -> None:
        doc = ProcessedDocument(raw_text="test")
        assert isinstance(doc.created_at, datetime)


class TestDocumentChunk:
    def test_default_metadata(self) -> None:
        chunk = DocumentChunk(text="Hello")
        assert chunk.metadata.document_type == "unknown"
        assert chunk.metadata.language == "en"
        assert chunk.metadata.chunk_version == "1.0.0"

    def test_custom_chunk_id(self) -> None:
        chunk = DocumentChunk(chunk_id="my_id", text="Hello")
        assert chunk.chunk_id == "my_id"

    def test_metadata_created_at_generated(self) -> None:
        chunk = DocumentChunk(text="Hello")
        assert isinstance(chunk.metadata.created_at, datetime)


# ---------------------------------------------------------------------------
# Multi-page Reports
# ---------------------------------------------------------------------------


class TestMultiPageReports:
    def test_cleaner_handles_page_separators(self, multi_page_text: str) -> None:
        cleaner = DefaultDocumentCleaner()
        result = cleaner.clean(multi_page_text)
        assert "--- Page 2 ---" not in result
        assert "Lab Results" in result

    def test_pipeline_handles_multi_page(self, multi_page_text: str) -> None:
        cfg = DocumentPipelineConfig(chunker_type="recursive", chunk_size=200, chunk_overlap=20)
        pipeline = DocumentPipeline(config=cfg)
        chunks = pipeline.process(
            raw_text=multi_page_text,
            report_id="rep_multi_page",
            page_count=2,
            provider="google_vision",
        )
        assert len(chunks) >= 1
        combined = " ".join(c.text for c in chunks)
        assert "IgE" in combined or "Eosinophil" in combined


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_very_short_document(self) -> None:
        pipeline = DocumentPipeline()
        chunks = pipeline.process(raw_text="Short text", report_id="rep_short")
        assert len(chunks) == 1
        assert "Short text" in chunks[0].text

    def test_very_long_document_respects_max_length(self) -> None:
        long_text = "word " * 50_000
        cfg = DocumentPipelineConfig(max_document_length=500)
        pipeline = DocumentPipeline(config=cfg)
        chunks = pipeline.process(raw_text=long_text, report_id="rep_long")
        assert len(chunks) >= 1

    def test_document_with_special_characters(self) -> None:
        text = "Patient: José García\nDiagnosis: Hypertension (stage 2)\nHbA1c: 7.2%"
        pipeline = DocumentPipeline()
        chunks = pipeline.process(raw_text=text, report_id="rep_special")
        assert len(chunks) >= 1

    def test_document_with_only_newlines(self) -> None:
        pipeline = DocumentPipeline()
        with pytest.raises(DocumentPipelineError):
            pipeline.process(raw_text="\n\n\n\n")

    def test_numeric_document(self) -> None:
        text = "12345 67890 11121 31415"
        pipeline = DocumentPipeline()
        chunks = pipeline.process(raw_text=text, report_id="rep_numeric")
        assert len(chunks) >= 1
        assert chunks[0].metadata.document_type == "unknown"

    def test_chunkers_produce_deterministic_output(self, sample_ocr_text: str) -> None:
        cleaner = DefaultDocumentCleaner()
        cleaned = cleaner.clean(sample_ocr_text)
        doc = ProcessedDocument(raw_text=sample_ocr_text, cleaned_text=cleaned)

        chunker = RecursiveChunker()
        config = DocumentPipelineConfig(chunker_type="recursive", chunk_size=200, chunk_overlap=20)

        chunks1 = chunker.chunk(doc, config)
        chunks2 = chunker.chunk(doc, config)

        assert len(chunks1) == len(chunks2)
        for c1, c2 in zip(chunks1, chunks2):
            assert c1.text == c2.text

    def test_preserves_document_metadata_through_pipeline(self, sample_ocr_text: str) -> None:
        pipeline = DocumentPipeline()
        chunks = pipeline.process(
            raw_text=sample_ocr_text,
            patient_id="pat_custom",
            report_id="rep_custom",
            source="test_upload",
            language="en",
            provider="test_provider",
            page_count=3,
        )
        for c in chunks:
            assert c.metadata.patient_id == "pat_custom"
            assert c.metadata.report_id == "rep_custom"
            assert c.metadata.source == "test_upload"
            assert c.metadata.language == "en"
            assert c.metadata.provider == "test_provider"
