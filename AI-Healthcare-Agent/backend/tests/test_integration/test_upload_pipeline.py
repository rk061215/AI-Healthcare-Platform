from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from app.database.enums import ReportStatus
from app.models.report import Report
from app.document_pipeline import DocumentPipeline, DocumentPipelineConfig
from app.document_pipeline.pipeline import (
    SimpleDocumentClassifier,
    SimpleSectionDetector,
)
from app.medical_parser.extractor import extract as med_parse
from app.medical_parser.schemas import SourceType
from app.ocr.engine import OcrEngine
from app.vector_store.vector_service import VectorService


class TestOcrPipeline:
    def test_ocr_engine_initialization(self):
        engine = OcrEngine(use_mock=True)
        assert engine is not None
        assert engine.primary is not None

    def test_mock_ocr_processes_image(self, sample_ocr_text):
        import tempfile
        from pathlib import Path
        engine = OcrEngine(use_mock=True)
        tmp = Path(tempfile.mkdtemp()) / "test.png"
        from PIL import Image
        img = Image.new("RGB", (100, 30), color="white")
        img.save(tmp)
        result = engine.process_document(tmp, "png")
        assert result is not None
        assert result.status == "completed" or result.status == "failed"
        if result.status == "completed":
            assert result.full_text

    def test_mock_ocr_processes_pdf(self, sample_ocr_text):
        import tempfile
        from pathlib import Path
        engine = OcrEngine(use_mock=True)
        tmp = Path(tempfile.mkdtemp()) / "test.pdf"
        tmp.write_bytes(sample_ocr_text.encode())
        result = engine.process_document(tmp, "pdf")
        assert result is not None

    def test_mock_ocr_multiline_output(self, sample_ocr_text):
        import tempfile
        from pathlib import Path
        from PIL import Image
        engine = OcrEngine(use_mock=True)
        tmp = Path(tempfile.mkdtemp()) / "test.png"
        img = Image.new("RGB", (100, 30), color="white")
        img.save(tmp)
        result = engine.process_document(tmp, "png")
        assert result is not None


class TestMedicalParserPipeline:
    def test_ai_extraction_from_ocr(self, sample_ocr_text, mock_ai_provider):
        schema, context = med_parse(sample_ocr_text, provider=mock_ai_provider)
        assert schema is not None
        assert schema.patient_name == "John Doe"
        assert schema.diagnosis == "Hypertension"
        assert len(schema.medications) >= 1
        assert schema.medications[0].name == "Lisinopril"
        assert context.source == SourceType.AI

    def test_regex_fallback(self, mock_ai_provider):
        ocr_text = """
Patient Name: Jane Smith
DOB: 1985-03-10
Diagnosis: Asthma
Medications:
Albuterol 90mcg 2 puffs as needed
Fluticasone 250mcg once daily
Lab Results:
IgE 250 IU/mL
"""
        failing_provider = MockAIProviderThatFails()
        schema, context = med_parse(ocr_text, provider=failing_provider)
        assert schema is not None

    def test_empty_ocr_raises(self, mock_ai_provider):
        with pytest.raises(Exception):
            med_parse("", provider=mock_ai_provider)

    def test_structured_report_schema_validation(self, sample_ocr_text, mock_ai_provider):
        schema, context = med_parse(sample_ocr_text, provider=mock_ai_provider)
        assert schema.patient_name
        assert schema.diagnosis
        assert schema.document_date
        assert hasattr(schema, "medications")
        assert hasattr(schema, "lab_results")


class TestDocumentPipeline:
    def test_document_pipeline_processes_text(self, sample_ocr_text):
        pipeline = DocumentPipeline(
            config=DocumentPipelineConfig(chunk_size=200, chunk_overlap=20),
        )
        chunks = pipeline.process(
            raw_text=sample_ocr_text,
            patient_id="test-patient",
            report_id="test-report",
            source="ocr",
        )
        assert chunks is not None
        assert len(chunks) > 0
        for c in chunks:
            assert c.text
            assert c.metadata.patient_id == "test-patient"

    def test_chunk_generation(self, sample_ocr_text):
        pipeline = DocumentPipeline(
            config=DocumentPipelineConfig(chunk_size=200, chunk_overlap=20),
        )
        chunks = pipeline.process(
            raw_text=sample_ocr_text,
            patient_id="p1",
            report_id="r1",
        )
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.text
            assert chunk.metadata.patient_id == "p1"
            assert chunk.metadata.report_id == "r1"

    def test_chunk_metadata_completeness(self, sample_ocr_text):
        pipeline = DocumentPipeline(
            config=DocumentPipelineConfig(chunk_size=200, chunk_overlap=20),
        )
        chunks = pipeline.process(
            raw_text=sample_ocr_text,
            patient_id="p1",
            report_id="r1",
            source="ocr",
            language="en",
        )
        for chunk in chunks:
            meta = chunk.metadata
            assert meta.chunk_index >= 0
            assert meta.source == "ocr"

    def test_section_detection(self, sample_ocr_text):
        detector = SimpleSectionDetector()
        sections = detector.detect_sections(sample_ocr_text)
        assert len(sections) > 0
        assert any("medication" in k.lower() for k in sections)
        assert any("diagnosis" in k.lower() for k in sections)

    def test_document_classification(self, sample_ocr_text):
        classifier = SimpleDocumentClassifier()
        doc_type = classifier.classify(sample_ocr_text)
        assert doc_type is not None
        assert isinstance(doc_type, str)


class TestEmbeddingPipeline:
    def test_embedding_service_embed(self, mock_embedding_service):
        vector, meta = mock_embedding_service.embed("Test medical text")
        assert len(vector) == 128
        assert meta.embedding_version == "1.0"

    def test_embedding_service_batch(self, mock_embedding_service):
        texts = ["Text one", "Text two", "Text three"]
        vectors, metas = mock_embedding_service.embed_batch(texts)
        assert len(vectors) == 3
        assert len(metas) == 3
        for v in vectors:
            assert len(v) == 128

    def test_vector_store_index_and_search(self, mock_vector_store, mock_embedding_service):
        vs = VectorService(store=mock_vector_store, embedding_service=mock_embedding_service)
        ids = vs.index_text("Metformin 500mg for diabetes", doc_id="doc1")
        assert len(ids) > 0
        results = vs.search("diabetes medication", k=5)
        assert len(results) >= 1
        assert hasattr(results[0], "score")

    def test_vector_store_patient_filter(self, mock_vector_store, mock_embedding_service):
        vs = VectorService(store=mock_vector_store, embedding_service=mock_embedding_service)
        vs.index_text("Lisinopril 10mg", doc_id="d1")
        results = vs.search_by_patient(patient_id="test-patient", query="medication")
        assert len(results) >= 1


class TestFullUploadPipeline:
    def test_upload_pdf_via_api(self, client, patient_auth_headers, sample_pdf_bytes):
        response = client.post(
            "/api/v1/documents/upload",
            headers=patient_auth_headers,
            files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
        )
        assert response.status_code in (200, 201, 202), f"Upload failed: {response.text}"

    def test_upload_image_via_api(self, client, patient_auth_headers, sample_image_bytes):
        response = client.post(
            "/api/v1/documents/upload",
            headers=patient_auth_headers,
            files={"file": ("test.png", sample_image_bytes, "image/png")},
        )
        assert response.status_code in (200, 201, 202), f"Image upload failed: {response.text}"

    def test_upload_invalid_file_rejected(self, client, patient_auth_headers):
        response = client.post(
            "/api/v1/documents/upload",
            headers=patient_auth_headers,
            files={"file": ("test.txt", b"not a valid file", "text/plain")},
        )
        assert response.status_code in (400, 422, 415), f"Expected rejection, got {response.status_code}"

    def test_database_persistence_after_upload(self, db_session, sample_ocr_text, mock_ai_provider):
        schema, context = med_parse(sample_ocr_text, provider=mock_ai_provider)
        now = datetime.now(timezone.utc)
        report = Report(
            id=uuid.uuid4(),
            patient_id=uuid.uuid4(),
            title=schema.document_type or "Prescription",
            file_path="/tmp/test.pdf",
            file_type="pdf",
            file_size=1024,
            ocr_text=sample_ocr_text,
            extracted_data=schema.model_dump() if hasattr(schema, "model_dump") else {},
            status=ReportStatus.COMPLETED,
            uploaded_at=now,
        )
        db_session.add(report)
        db_session.commit()
        saved = db_session.query(Report).filter_by(id=report.id).first()
        assert saved is not None
        assert saved.status == ReportStatus.COMPLETED
        assert saved.ocr_text == sample_ocr_text

    def test_ocr_to_parse_to_chunk_pipeline(self, sample_ocr_text, mock_ai_provider):
        schema, context = med_parse(sample_ocr_text, provider=mock_ai_provider)
        pipeline = DocumentPipeline(
            config=DocumentPipelineConfig(chunk_size=200, chunk_overlap=20),
        )
        chunks = pipeline.process(
            raw_text=sample_ocr_text,
            patient_id="p1",
            report_id="r1",
        )
        assert len(chunks) >= 1
        assert schema.patient_name


class MockAIProviderThatFails:
    name = "mock_failing"
    _call_count = 0

    def generate_structured_output(self, prompt, output_schema, system_prompt=None):
        self._call_count += 1
        if self._call_count <= 2:
            raise RuntimeError(f"Simulated failure #{self._call_count}")
        return {}

    def generate_text(self, prompt, system_prompt=None):
        return ""

    async def stream_response(self, prompt, system_prompt=None):
        yield ""
        raise StopAsyncIteration

    def generate_embeddings(self, texts):
        return [[0.1, 0.2, 0.3]]

    def count_tokens(self, text):
        return len(text.split())

    def health_check(self):
        return {"status": "healthy"}

    def initialize(self):
        pass

    def close(self):
        pass
