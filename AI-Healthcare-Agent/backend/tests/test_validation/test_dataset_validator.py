import pytest
from app.validation.dataset.dataset_validator import DatasetValidator, ValidationResult
from app.validation.dataset.ground_truth import (
    DocumentType,
    DifficultyLevel,
    GroundTruth,
    GroundTruthEntry,
    GroundTruthSet,
    QuestionCategory,
)


class TestDatasetValidator:
    def _make_valid_set(self) -> GroundTruthSet:
        gts = GroundTruthSet(name="valid_set")
        doc = GroundTruth(document_id="d1", document_type=DocumentType.CBC_REPORT, document_text="CBC data")
        doc.add_entry(GroundTruthEntry(question="Q1?", expected_answer="A1"))
        gts.add_document(doc)
        return gts

    def test_valid_dataset(self):
        result = DatasetValidator.validate(self._make_valid_set())
        assert result.is_valid

    def test_empty_name(self):
        gts = self._make_valid_set()
        gts.name = ""
        result = DatasetValidator.validate(gts)
        assert not result.is_valid
        assert any("name" in e for e in result.errors)

    def test_no_documents(self):
        gts = GroundTruthSet(name="empty")
        result = DatasetValidator.validate(gts)
        assert not result.is_valid
        assert any("at least one document" in e for e in result.errors)

    def test_empty_question(self):
        doc = GroundTruth(document_id="d1", document_type=DocumentType.CBC_REPORT, document_text="t")
        doc.add_entry(GroundTruthEntry(question="", expected_answer="A1"))
        gts = GroundTruthSet(name="test")
        gts.add_document(doc)
        result = DatasetValidator.validate(gts)
        assert not result.is_valid

    def test_confidence_out_of_range(self):
        doc = GroundTruth(document_id="d1", document_type=DocumentType.CBC_REPORT, document_text="t")
        doc.add_entry(GroundTruthEntry(question="Q?", expected_answer="A", expected_confidence=1.5))
        gts = GroundTruthSet(name="test")
        gts.add_document(doc)
        result = DatasetValidator.validate(gts)
        assert not result.is_valid

    def test_confidence_negative(self):
        doc = GroundTruth(document_id="d1", document_type=DocumentType.CBC_REPORT, document_text="t")
        doc.add_entry(GroundTruthEntry(question="Q?", expected_answer="A", expected_confidence=-0.5))
        gts = GroundTruthSet(name="test")
        gts.add_document(doc)
        result = DatasetValidator.validate(gts)
        assert not result.is_valid

    def test_duplicate_document_id(self):
        gts = GroundTruthSet(name="test")
        doc1 = GroundTruth(document_id="d1", document_type=DocumentType.CBC_REPORT, document_text="t")
        doc1.add_entry(GroundTruthEntry(question="Q1", expected_answer="A1"))
        doc2 = GroundTruth(document_id="d1", document_type=DocumentType.LIPID_PROFILE, document_text="t")
        doc2.add_entry(GroundTruthEntry(question="Q2", expected_answer="A2"))
        gts.add_document(doc1)
        gts.add_document(doc2)
        result = DatasetValidator.validate(gts)
        assert result.is_valid
        assert any("Duplicate" in w for w in result.warnings)

    def test_warning_for_short_answer(self):
        doc = GroundTruth(document_id="d1", document_type=DocumentType.CBC_REPORT, document_text="t")
        doc.add_entry(GroundTruthEntry(question="Q?", expected_answer=""))
        gts = GroundTruthSet(name="test")
        gts.add_document(doc)
        result = DatasetValidator.validate(gts)
        assert any("empty expected_answer" in w for w in result.warnings)

    def test_validation_result_dict(self):
        vr = ValidationResult()
        vr.add_error("err1")
        vr.add_warning("warn1")
        d = vr.dict()
        assert d["is_valid"] is False
        assert d["error_count"] == 1
        assert d["warning_count"] == 1
        assert d["errors"] == ["err1"]
