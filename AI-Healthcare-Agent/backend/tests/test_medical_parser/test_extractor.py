import pytest

from app.medical_parser.exceptions import EmptyOCRError, RegexExtractorError, RetryExhaustedError
from app.medical_parser.extractor import AIExtractor, RegexExtractor, extract
from app.medical_parser.schemas import ExtractionContext
from app.medical_parser.types import SourceType
from tests.test_medical_parser.conftest import MockProvider


class TestRegexExtractor:
    def test_extract_patient_name(self, sample_ocr_text):
        ctx = ExtractionContext()
        schema = RegexExtractor().extract(sample_ocr_text, ctx)
        assert schema.patient_name == "John Doe"
        assert ctx.source == SourceType.REGEX

    def test_extract_dob(self, sample_ocr_text):
        schema = RegexExtractor().extract(sample_ocr_text, ExtractionContext())
        assert schema.date_of_birth == "1990-05-20"

    def test_extract_document_date(self, sample_ocr_text):
        schema = RegexExtractor().extract(sample_ocr_text, ExtractionContext())
        assert schema.document_date == "2026-01-15"

    def test_extract_doctor_name(self, sample_ocr_text):
        schema = RegexExtractor().extract(sample_ocr_text, ExtractionContext())
        assert schema.doctor_name == "Sarah Smith"

    def test_extract_hospital_name(self, sample_ocr_text):
        schema = RegexExtractor().extract(sample_ocr_text, ExtractionContext())
        assert schema.hospital_name == "General Hospital"

    def test_extract_diagnosis(self, sample_ocr_text):
        schema = RegexExtractor().extract(sample_ocr_text, ExtractionContext())
        assert "Diabetes" in schema.diagnosis

    def test_extract_medications(self, sample_ocr_text):
        schema = RegexExtractor().extract(sample_ocr_text, ExtractionContext())
        assert len(schema.medications) == 2
        assert schema.medications[0].name == "Metformin"
        assert schema.medications[0].dosage == "500mg"
        assert schema.medications[1].name == "Lisinopril"
        assert schema.medications[1].dosage == "10mg"

    def test_extract_lab_results(self, sample_ocr_text):
        schema = RegexExtractor().extract(sample_ocr_text, ExtractionContext())
        assert len(schema.lab_results) == 2
        assert schema.lab_results[0].test_name == "Blood Glucose"
        assert schema.lab_results[0].value == "126"
        assert schema.lab_results[0].unit == "mg/dL"

    def test_extract_follow_up_date(self, sample_ocr_text):
        schema = RegexExtractor().extract(sample_ocr_text, ExtractionContext())
        assert schema.follow_up_date == "2026-04-15"

    def test_extract_notes(self, sample_ocr_text):
        schema = RegexExtractor().extract(sample_ocr_text, ExtractionContext())
        assert "Monitor" in schema.doctor_instructions

    def test_empty_ocr_raises_error(self):
        with pytest.raises(EmptyOCRError):
            RegexExtractor().extract("", ExtractionContext())

    def test_whitespace_only_raises_error(self):
        with pytest.raises(EmptyOCRError):
            RegexExtractor().extract("   \n  \n  ", ExtractionContext())

    def test_multi_page_extraction(self, multi_page_ocr_text):
        schema = RegexExtractor().extract(multi_page_ocr_text, ExtractionContext())
        assert schema.patient_name == "Jane Smith"
        assert len(schema.medications) == 2
        assert schema.medications[0].name == "Albuterol"

    def test_no_text_returns_empty_fields(self):
        schema = RegexExtractor().extract("No relevant medical data here", ExtractionContext())
        assert schema.patient_name == ""
        assert schema.diagnosis == ""
        assert len(schema.medications) == 0


class TestAIExtractor:
    def test_extract_success(self):
        provider = MockProvider()
        ctx = ExtractionContext()
        schema = AIExtractor(provider=provider).extract("Patient: John\nDiagnosis: Flu", ctx)
        assert schema.patient_name == "John Doe"
        assert schema.diagnosis == "Hypertension"
        assert len(schema.medications) == 1
        assert ctx.source == SourceType.AI

    def test_retry_on_failure_succeeds_eventually(self):
        provider = MockProvider(fail_count=2)  # fail twice, succeed on 3rd
        ctx = ExtractionContext()
        schema = AIExtractor(provider=provider, max_retries=3).extract(
            "Patient: John\nDiagnosis: Flu", ctx
        )
        assert schema.patient_name == "John Doe"
        assert provider._call_count == 3

    def test_retry_exhausted_raises_error(self):
        provider = MockProvider(fail_count=5)  # always fails
        with pytest.raises(RetryExhaustedError):
            AIExtractor(provider=provider, max_retries=2).extract(
                "Patient: John\nDiagnosis: Flu", ExtractionContext()
            )

    def test_empty_ocr_raises_error(self, mock_provider):
        with pytest.raises(EmptyOCRError):
            AIExtractor(provider=mock_provider).extract("", ExtractionContext())

    def test_return_value_is_validated(self):
        provider = MockProvider(return_value={"patient_name": "Alice"})
        ctx = ExtractionContext()
        schema = AIExtractor(provider=provider).extract("some text", ctx)
        assert schema.patient_name == "Alice"


class TestExtractEntryPoint:
    def test_fallback_to_regex_on_ai_failure(self, sample_ocr_text):
        provider = MockProvider(fail_count=5)
        schema, ctx = extract(sample_ocr_text, provider, max_retries=1)
        assert schema.patient_name == "John Doe"
        assert ctx.source == SourceType.REGEX  # fell back
        assert len(ctx.validation_errors) > 0

    def test_ai_success_no_fallback(self, sample_ocr_text, mock_provider):
        schema, ctx = extract(sample_ocr_text, mock_provider)
        assert ctx.source == SourceType.AI
        assert len(ctx.validation_errors) == 0

    def test_empty_ocr_propagates_error(self, mock_provider):
        with pytest.raises(RegexExtractorError, match="AI extraction failed"):
            extract("", mock_provider)

    def test_regex_only_extraction_no_ai(self, sample_ocr_text):
        """Extract using only regex via the entry point when AI is not available."""
        from app.medical_parser.extractor import RegexExtractor
        ctx = ExtractionContext()
        schema = RegexExtractor().extract(sample_ocr_text, ctx)
        assert schema.patient_name is not None
        assert schema.diagnosis is not None
