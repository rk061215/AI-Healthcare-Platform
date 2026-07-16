import pytest

from app.medical_parser.schemas import (
    LabResultExtracted,
    MedicalReportSchema,
    MedicationExtracted,
)
from app.medical_parser.validator import validate, validate_with_retry
from tests.test_medical_parser.conftest import MockProvider


class TestValidation:
    def test_valid_schema_passes(self):
        schema = MedicalReportSchema(
            patient_name="John Doe",
            diagnosis="Hypertension",
            medications=[MedicationExtracted(name="Lisinopril", dosage="10mg")],
        )
        result = validate(schema)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_missing_patient_name(self):
        schema = MedicalReportSchema(
            diagnosis="Hypertension",
            medications=[MedicationExtracted(name="Lisinopril")],
        )
        result = validate(schema)
        assert result.is_valid is False
        assert "patient_name" in result.missing_required

    def test_missing_diagnosis(self):
        schema = MedicalReportSchema(
            patient_name="John Doe",
            medications=[MedicationExtracted(name="Lisinopril")],
        )
        result = validate(schema)
        assert result.is_valid is False
        assert "diagnosis" in result.missing_required

    def test_missing_medications(self):
        schema = MedicalReportSchema(
            patient_name="John Doe",
            diagnosis="Hypertension",
        )
        result = validate(schema)
        assert result.is_valid is False
        assert "medications" in result.missing_required

    def test_empty_string_fields(self):
        schema = MedicalReportSchema(
            patient_name="",
            diagnosis="  ",
            medications=[MedicationExtracted(name="Lisinopril")],
        )
        result = validate(schema)
        assert result.is_valid is False
        assert len(result.missing_required) == 2

    def test_invalid_document_type(self):
        schema = MedicalReportSchema(
            document_type="INVALID",
            patient_name="John",
            diagnosis="Flu",
            medications=[MedicationExtracted(name="Tylenol")],
        )
        result = validate(schema)
        assert result.is_valid is False
        assert any("document_type" in e for e in result.errors)

    def test_valid_document_types(self):
        for doc_type in ["PRESCRIPTION", "LAB_REPORT", "GENERAL", "UNKNOWN"]:
            schema = MedicalReportSchema(
                document_type=doc_type,
                patient_name="John",
                diagnosis="Flu",
                medications=[MedicationExtracted(name="Tylenol")],
            )
            result = validate(schema)
            assert result.is_valid is True, f"Failed for {doc_type}: {result.errors}"

    def test_medication_empty_name(self):
        schema = MedicalReportSchema(
            patient_name="John",
            diagnosis="Flu",
            medications=[MedicationExtracted(name="", dosage="500mg")],
        )
        result = validate(schema)
        assert result.is_valid is False
        assert any("empty name" in e for e in result.errors)

    def test_medication_dosage_without_unit_warning(self):
        schema = MedicalReportSchema(
            patient_name="John",
            diagnosis="Flu",
            medications=[MedicationExtracted(name="Tylenol", dosage="500")],
        )
        result = validate(schema)
        assert result.is_valid is True  # warning, not error
        assert len(result.warnings) > 0
        assert any("dosage" in w for w in result.warnings)

    def test_lab_result_empty_name(self):
        schema = MedicalReportSchema(
            patient_name="John",
            diagnosis="Flu",
            medications=[MedicationExtracted(name="Tylenol")],
            lab_results=[LabResultExtracted(test_name="")],
        )
        result = validate(schema)
        assert result.is_valid is False
        assert any("empty test_name" in e for e in result.errors)

    def test_lab_result_missing_unit_warning(self):
        schema = MedicalReportSchema(
            patient_name="John",
            diagnosis="Flu",
            medications=[MedicationExtracted(name="Tylenol")],
            lab_results=[LabResultExtracted(test_name="Glucose", value="126")],
        )
        result = validate(schema)
        assert result.is_valid is True
        assert len(result.warnings) > 0

    def test_all_fields_empty(self):
        schema = MedicalReportSchema()
        result = validate(schema)
        assert result.is_valid is False
        assert any("All fields are empty" in e for e in result.errors)

    def test_date_format_warning(self):
        schema = MedicalReportSchema(
            patient_name="John",
            diagnosis="Flu",
            medications=[MedicationExtracted(name="Tylenol")],
            date_of_birth="not-a-date",
        )
        result = validate(schema)
        assert result.is_valid is True  # warning only
        assert any("date_of_birth" in w for w in result.warnings)

    def test_iso_date_passes_no_warning(self):
        schema = MedicalReportSchema(
            patient_name="John",
            diagnosis="Flu",
            medications=[MedicationExtracted(name="Tylenol")],
            date_of_birth="1990-01-15",
        )
        result = validate(schema)
        assert result.is_valid is True
        date_warnings = [w for w in result.warnings if "date_of_birth" in w]
        assert len(date_warnings) == 0


class TestValidateWithRetry:
    def test_first_attempt_succeeds(self, sample_ocr_text, mock_provider):
        def extract_fn():
            from app.medical_parser.extractor import RegexExtractor
            ctx = type("ctx", (), {})()
            schema = RegexExtractor().extract(sample_ocr_text, ctx)
            return schema, ctx

        schema, ctx, vr = validate_with_retry(sample_ocr_text, extract_fn)
        assert vr.is_valid is True
        assert schema.patient_name == "John Doe"
