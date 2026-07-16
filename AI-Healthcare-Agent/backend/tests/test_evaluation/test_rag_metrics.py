from __future__ import annotations

from app.evaluation.rag_metrics import (
    AnswerRelevanceMetric,
    CitationAccuracyMetric,
    ContextPrecisionMetric,
    ContextRecallMetric,
    DiagnosisAccuracyMetric,
    FollowUpAccuracyMetric,
    GroundednessMetric,
    LabResultAccuracyMetric,
    MedicationAccuracyMetric,
    answer_relevance,
    citation_accuracy,
    compute_all_rag_metrics,
    context_precision,
    context_recall,
    diagnosis_accuracy,
    follow_up_extraction_accuracy,
    groundedness,
    lab_result_accuracy,
    medication_extraction_accuracy,
)


class TestGroundedness:
    def test_fully_grounded(self) -> None:
        answer = "The patient has diabetes. They are taking metformin."
        context = ["Patient diagnosed with diabetes.", "Prescribed metformin 500mg."]
        score = groundedness(answer, context)
        assert score >= 0.5

    def test_no_context(self) -> None:
        score = groundedness("The patient has diabetes.", [])
        assert score == 0.0

    def test_empty_answer(self) -> None:
        assert groundedness("", ["context"]) == 0.0


class TestCitationAccuracy:
    def test_all_citations_valid(self) -> None:
        citations = [{"text": "Patient has diabetes"}, {"text": "Prescribed metformin"}]
        context = ["Patient has diabetes. Type 2.", "Prescribed metformin 500mg daily."]
        score = citation_accuracy(citations, context)
        assert score == 1.0

    def test_no_citations(self) -> None:
        assert citation_accuracy([], ["context"]) == 0.0

    def test_no_context(self) -> None:
        assert citation_accuracy([{"text": "test"}], []) == 0.0


class TestContextPrecision:
    def test_all_relevant(self) -> None:
        retrieved = ["a", "b", "c"]
        relevant = ["a", "b", "c"]
        assert context_precision(retrieved, relevant) == 1.0

    def test_empty_retrieved(self) -> None:
        assert context_precision([], ["a"]) == 0.0


class TestContextRecall:
    def test_all_retrieved(self) -> None:
        retrieved = ["a", "b", "c"]
        relevant = ["a", "b"]
        assert context_recall(retrieved, relevant) == 1.0

    def test_empty_relevant(self) -> None:
        assert context_recall(["a"], []) == 0.0

    def test_empty_retrieved(self) -> None:
        assert context_recall([], ["a"]) == 0.0


class TestAnswerRelevance:
    def test_some_relevance(self) -> None:
        answer = "The patient takes metformin for diabetes."
        question = "What medication does the patient take?"
        score = answer_relevance(answer, question)
        assert score > 0

    def test_no_relevance(self) -> None:
        answer = "The sky is blue."
        question = "What medication?"
        score = answer_relevance(answer, question)
        assert score == 0.0

    def test_empty_answer(self) -> None:
        assert answer_relevance("", "question") == 0.0

    def test_empty_question(self) -> None:
        assert answer_relevance("answer", "") == 0.0


class TestMedicationAccuracy:
    def test_exact_match(self) -> None:
        assert medication_extraction_accuracy(
            ["metformin", "insulin"],
            ["metformin", "insulin"],
        ) == 1.0

    def test_partial_match(self) -> None:
        assert medication_extraction_accuracy(
            ["metformin", "insulin"],
            ["metformin"],
        ) == 0.5

    def test_no_extracted(self) -> None:
        assert medication_extraction_accuracy(["metformin"], []) == 0.0

    def test_empty_expected(self) -> None:
        assert medication_extraction_accuracy([], ["metformin"]) == 0.0


class TestDiagnosisAccuracy:
    def test_exact_match(self) -> None:
        assert diagnosis_accuracy(
            ["Diabetes Type 2", "Hypertension"],
            ["Diabetes Type 2", "Hypertension"],
        ) == 1.0


class TestLabResultAccuracy:
    def test_exact_match(self) -> None:
        expected = [{"name": "Glucose", "value": "95"}, {"name": "HbA1c", "value": "5.7"}]
        extracted = [{"name": "Glucose", "value": "95"}, {"name": "HbA1c", "value": "5.7"}]
        assert lab_result_accuracy(expected, extracted) == 1.0

    def test_no_extracted(self) -> None:
        expected = [{"name": "Glucose", "value": "95"}]
        assert lab_result_accuracy(expected, []) == 0.0


class TestFollowUpAccuracy:
    def test_exact_match(self) -> None:
        assert follow_up_extraction_accuracy(
            ["Follow up in 3 months", "Monitor blood pressure"],
            ["Follow up in 3 months", "Monitor blood pressure"],
        ) == 1.0


class TestGroundednessMetric:
    def test_evaluate(self) -> None:
        metric = GroundednessMetric()
        result = metric.evaluate(
            answer="Patient has diabetes.",
            context_chunks=["Patient has diabetes."],
        )
        assert result.metric_name == "Groundedness"
        assert result.category == "rag"
        assert result.score > 0


class TestCitationAccuracyMetric:
    def test_evaluate(self) -> None:
        metric = CitationAccuracyMetric()
        result = metric.evaluate(
            citations=[{"text": "diabetes"}],
            context_chunks=["Patient has diabetes"],
        )
        assert result.score > 0


class TestContextPrecisionMetric:
    def test_evaluate(self) -> None:
        metric = ContextPrecisionMetric()
        result = metric.evaluate(
            retrieved_chunks=["a", "b"],
            relevant_chunks=["a"],
        )
        assert result.score == 0.5


class TestContextRecallMetric:
    def test_evaluate(self) -> None:
        metric = ContextRecallMetric()
        result = metric.evaluate(
            retrieved_chunks=["a", "b"],
            relevant_chunks=["a", "c"],
        )
        assert result.score == 0.5


class TestAnswerRelevanceMetric:
    def test_evaluate(self) -> None:
        metric = AnswerRelevanceMetric()
        result = metric.evaluate(
            answer="The patient is prescribed medication metformin for diabetes medication.",
            question="What medication is the patient taking?",
        )
        assert result.metric_name == "Answer Relevance"
        assert result.score > 0


class TestMedicationAccuracyMetric:
    def test_evaluate(self) -> None:
        metric = MedicationAccuracyMetric()
        result = metric.evaluate(
            expected_medications=["metformin"],
            extracted_medications=["metformin"],
        )
        assert result.score == 1.0


class TestDiagnosisAccuracyMetric:
    def test_evaluate(self) -> None:
        metric = DiagnosisAccuracyMetric()
        result = metric.evaluate(
            expected_diagnoses=["Diabetes"],
            extracted_diagnoses=["Diabetes"],
        )
        assert result.score == 1.0


class TestLabResultAccuracyMetric:
    def test_evaluate(self) -> None:
        metric = LabResultAccuracyMetric()
        result = metric.evaluate(
            expected_lab_results=[{"name": "Glucose", "value": "95"}],
            extracted_lab_results=[{"name": "Glucose", "value": "95"}],
        )
        assert result.score == 1.0


class TestFollowUpAccuracyMetric:
    def test_evaluate(self) -> None:
        metric = FollowUpAccuracyMetric()
        result = metric.evaluate(
            expected_follow_ups=["Follow up in 3 months"],
            extracted_follow_ups=["Follow up in 3 months"],
        )
        assert result.score == 1.0


class TestComputeAllRagMetrics:
    def test_basic_computation(self) -> None:
        results = compute_all_rag_metrics(
            answers=["Patient takes metformin for diabetes."],
            questions=["What medication?"],
            contexts=[["Patient takes metformin", "Has diabetes"]],
            relevant_chunks_list=[["Patient takes metformin"]],
            citations_list=[[{"text": "Patient takes metformin"}]],
        )
        assert len(results) >= 4
        result_names = [r.metric_name for r in results]
        assert "Groundedness" in result_names
        assert "Answer Relevance" in result_names
        assert "Context Precision" in result_names
        assert "Context Recall" in result_names
        assert "Citation Accuracy" in result_names

    def test_empty_lists(self) -> None:
        results = compute_all_rag_metrics([], [], [], [], [])
        assert results == []
