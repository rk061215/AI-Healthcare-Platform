import pytest
from app.validation.evaluation.clinical_test_runner import ClinicalTestRunner, ClinicalTestCase
from app.validation.dataset.ground_truth import (
    DocumentType,
    DifficultyLevel,
    GroundTruth,
    GroundTruthEntry,
    GroundTruthSet,
    QuestionCategory,
)


class TestClinicalTestRunner:
    def _make_answer_fn(self):
        answers = {
            "What is WBC?": "WBC is 8.5",
            "Are there abnormalities?": "All normal",
        }
        def fn(q: str) -> dict:
            return {
                "answer": answers.get(q, f"Answer to: {q}"),
                "citations": ["doc_001:wbc"] if q == "What is WBC?" else ["doc_001:section"],
            }
        return fn

    def _make_dataset(self) -> GroundTruthSet:
        gts = GroundTruthSet(name="clinical_test")
        doc = GroundTruth(
            document_id="doc_001",
            document_type=DocumentType.CBC_REPORT,
            document_text="CBC data",
        )
        doc.add_entry(GroundTruthEntry(
            question="What is WBC?",
            expected_answer="WBC is 8.5",
            expected_citations=["doc_001:wbc"],
            difficulty=DifficultyLevel.EASY,
            category=QuestionCategory.LAB_RESULT,
        ))
        doc.add_entry(GroundTruthEntry(
            question="Are there abnormalities?",
            expected_answer="All normal",
            difficulty=DifficultyLevel.MEDIUM,
            category=QuestionCategory.DIAGNOSIS,
        ))
        gts.add_document(doc)
        return gts

    def test_run(self):
        runner = ClinicalTestRunner()
        dataset = self._make_dataset()
        summary = runner.run(dataset, self._make_answer_fn(), "test_run")
        assert summary.total == 2
        assert summary.passed >= 1
        assert summary.test_name == "test_run"

    def test_run_with_empty_dataset(self):
        runner = ClinicalTestRunner()
        gts = GroundTruthSet(name="empty")
        summary = runner.run(gts, self._make_answer_fn())
        assert summary.total == 0
        assert summary.passed == 0

    def test_score_answer_match(self):
        runner = ClinicalTestRunner()
        score = runner._score_answer_match("WBC is 8.5 per uL", "WBC is 8.5")
        assert score > 0.5

    def test_score_answer_match_empty(self):
        runner = ClinicalTestRunner()
        assert runner._score_answer_match("", "expected") == 0.0
        assert runner._score_answer_match("actual", "") == 0.0
        assert runner._score_answer_match("", "") == 1.0

    def test_score_citations(self):
        runner = ClinicalTestRunner()
        assert runner._score_citations(["a", "b"], ["a", "c"]) == 0.5
        assert runner._score_citations([], ["a"]) == 0.0
        assert runner._score_citations(["a"], []) == 1.0

    def test_summary_by_difficulty(self):
        runner = ClinicalTestRunner()
        dataset = self._make_dataset()
        summary = runner.run(dataset, self._make_answer_fn())
        assert "easy" in summary.by_difficulty
        assert "medium" in summary.by_difficulty

    def test_summary_by_category(self):
        runner = ClinicalTestRunner()
        dataset = self._make_dataset()
        summary = runner.run(dataset, self._make_answer_fn())
        assert "lab_result" in summary.by_category

    def test_handles_answer_fn_error(self):
        def failing_fn(q):
            raise ValueError("LLM error")
        runner = ClinicalTestRunner()
        dataset = self._make_dataset()
        summary = runner.run(dataset, failing_fn)
        assert summary.total == 2
        assert summary.passed == 0
        assert len(summary.errors) >= 1
