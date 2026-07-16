import pytest
from app.validation.dataset.ground_truth import (
    DocumentType,
    DifficultyLevel,
    QuestionCategory,
    GroundTruthEntry,
    GroundTruth,
    GroundTruthSet,
    MetricName,
)


class TestGroundTruthEntry:
    def test_create_entry(self):
        entry = GroundTruthEntry(
            question="What is hemoglobin?",
            expected_answer="Hemoglobin is 14.2 g/dL",
            expected_citations=["cbc_001:hemoglobin"],
            difficulty=DifficultyLevel.EASY,
            category=QuestionCategory.LAB_RESULT,
        )
        assert entry.question == "What is hemoglobin?"
        assert entry.difficulty == DifficultyLevel.EASY
        assert entry.category == QuestionCategory.LAB_RESULT

    def test_defaults(self):
        entry = GroundTruthEntry(question="test", expected_answer="answer")
        assert entry.difficulty == DifficultyLevel.MEDIUM
        assert entry.category == QuestionCategory.DIAGNOSIS
        assert entry.expected_confidence == 0.9
        assert entry.expected_citations == []
        assert entry.expected_medical_concepts == []


class TestGroundTruth:
    def test_create_document(self):
        doc = GroundTruth(
            document_id="cbc_001",
            document_type=DocumentType.CBC_REPORT,
            document_text="CBC results...",
        )
        assert doc.document_id == "cbc_001"
        assert doc.document_type == DocumentType.CBC_REPORT
        assert doc.version == "1.0.0"

    def test_add_entry(self):
        doc = GroundTruth(
            document_id="cbc_001",
            document_type=DocumentType.CBC_REPORT,
            document_text="test",
        )
        entry = GroundTruthEntry(question="Q1", expected_answer="A1")
        doc.add_entry(entry)
        assert len(doc.entries) == 1

    def test_filter_by_difficulty(self):
        doc = GroundTruth(document_id="d1", document_type=DocumentType.CBC_REPORT, document_text="t")
        doc.add_entry(GroundTruthEntry(question="e1", expected_answer="a1", difficulty=DifficultyLevel.EASY))
        doc.add_entry(GroundTruthEntry(question="e2", expected_answer="a2", difficulty=DifficultyLevel.HARD))
        doc.add_entry(GroundTruthEntry(question="e3", expected_answer="a3", difficulty=DifficultyLevel.EASY))
        easy = doc.filter_by_difficulty(DifficultyLevel.EASY)
        assert len(easy) == 2
        hard = doc.filter_by_difficulty(DifficultyLevel.HARD)
        assert len(hard) == 1

    def test_filter_by_category(self):
        doc = GroundTruth(document_id="d1", document_type=DocumentType.PRESCRIPTION, document_text="t")
        doc.add_entry(GroundTruthEntry(question="q1", expected_answer="a1", category=QuestionCategory.MEDICATION))
        doc.add_entry(GroundTruthEntry(question="q2", expected_answer="a2", category=QuestionCategory.DOSAGE))
        meds = doc.filter_by_category(QuestionCategory.MEDICATION)
        assert len(meds) == 1


class TestGroundTruthSet:
    def test_empty_set(self):
        gts = GroundTruthSet(name="test")
        assert gts.count() == 0
        assert gts.all_entries() == []

    def test_add_document(self):
        gts = GroundTruthSet(name="test")
        doc = GroundTruth(document_id="d1", document_type=DocumentType.CBC_REPORT, document_text="t")
        doc.add_entry(GroundTruthEntry(question="q1", expected_answer="a1"))
        gts.add_document(doc)
        assert gts.count() == 1

    def test_stats(self):
        gts = GroundTruthSet(name="test_stats")
        doc = GroundTruth(document_id="d1", document_type=DocumentType.CBC_REPORT, document_text="t")
        doc.add_entry(GroundTruthEntry(question="q1", expected_answer="a1", difficulty=DifficultyLevel.EASY, category=QuestionCategory.LAB_RESULT))
        doc.add_entry(GroundTruthEntry(question="q2", expected_answer="a2", difficulty=DifficultyLevel.HARD, category=QuestionCategory.DIAGNOSIS))
        gts.add_document(doc)
        stats = gts.stats()
        assert stats["total_documents"] == 1
        assert stats["total_entries"] == 2
        assert stats["by_difficulty"]["easy"] == 1
        assert stats["by_difficulty"]["hard"] == 1
        assert stats["by_category"]["lab_result"] == 1

    def test_multiple_documents(self):
        gts = GroundTruthSet(name="multi")
        for i in range(3):
            doc = GroundTruth(document_id=f"d{i}", document_type=DocumentType.CLINICAL_NOTES, document_text="t")
            doc.add_entry(GroundTruthEntry(question=f"q{i}", expected_answer=f"a{i}"))
            gts.add_document(doc)
        assert gts.count() == 3
        assert len(gts.documents) == 3


class TestEnums:
    def test_document_types(self):
        types = [dt.value for dt in DocumentType]
        assert "prescription" in types
        assert "cbc_report" in types
        assert "lipid_profile" in types
        assert "clinical_notes" in types
        assert len(types) == 10

    def test_difficulty_levels(self):
        assert DifficultyLevel.EASY.value == "easy"
        assert DifficultyLevel.EXPERT.value == "expert"

    def test_question_categories(self):
        assert QuestionCategory.DIAGNOSIS.value == "diagnosis"
        assert QuestionCategory.REFERRAL.value == "referral"

    def test_metric_names(self):
        assert MetricName.RETRIEVAL_RECALL.value == "retrieval_recall"
        assert MetricName.TOKEN_USAGE.value == "token_usage"
