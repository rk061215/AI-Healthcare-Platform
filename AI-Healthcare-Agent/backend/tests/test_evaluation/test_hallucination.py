from __future__ import annotations

from app.evaluation.hallucination import (
    HallucinationRateMetric,
    compute_all_hallucination_metrics,
    contains_hallucination_patterns,
    contains_unsupported_medical_claims,
    detect_hallucinated_claims,
    hallucination_rate,
)


class TestDetectHallucinatedClaims:
    def test_no_hallucinations(self) -> None:
        answer = "Based on the records, the patient has diabetes."
        context = ["Patient has diabetes.", "Blood sugar levels are elevated."]
        claims = detect_hallucinated_claims(answer, context)
        assert len(claims) == 0

    def test_hallucinated_claim(self) -> None:
        answer = "The patient has a rare genetic disorder that affects calcium metabolism."
        context = ["Blood glucose levels are within normal range.", "HbA1c is 5.4%."]
        claims = detect_hallucinated_claims(answer, context)
        assert len(claims) > 0

    def test_empty_answer(self) -> None:
        assert detect_hallucinated_claims("", ["context"]) == []


class TestHallucinationRate:
    def test_no_hallucinations(self) -> None:
        rate = hallucination_rate(
            "The patient has diabetes.",
            ["Patient has diabetes."],
        )
        assert rate == 0.0

    def test_all_hallucinated(self) -> None:
        rate = hallucination_rate(
            "The patient has a rare disease.",
            ["Blood test results are normal."],
        )
        assert rate > 0.0

    def test_empty_answer(self) -> None:
        assert hallucination_rate("", ["context"]) == 0.0


class TestContainsHallucinationPatterns:
    def test_no_patterns(self) -> None:
        matches = contains_hallucination_patterns("The patient has diabetes.")
        assert matches == []

    def test_has_pattern(self) -> None:
        matches = contains_hallucination_patterns("This treatment is 100% effective.")
        assert len(matches) > 0


class TestContainsUnsupportedMedicalClaims:
    def test_no_claims(self) -> None:
        claims = contains_unsupported_medical_claims("The patient has diabetes.")
        assert claims == []

    def test_has_claim(self) -> None:
        claims = contains_unsupported_medical_claims("You should stop taking your medication.")
        assert len(claims) > 0


class TestHallucinationRateMetric:
    def test_evaluate(self) -> None:
        metric = HallucinationRateMetric()
        result = metric.evaluate(
            answer="The patient has diabetes.",
            context_chunks=["Patient has diabetes."],
        )
        assert result.metric_name == "Hallucination Rate"
        assert result.category == "hallucination"
        assert result.score > 0.5

    def test_evaluate_no_data(self) -> None:
        metric = HallucinationRateMetric()
        result = metric.evaluate()
        assert result.score == 1.0


class TestComputeAllHallucinationMetrics:
    def test_basic_computation(self) -> None:
        results = compute_all_hallucination_metrics(
            answers=["Patient has diabetes."],
            contexts=[["Patient has diabetes."]],
        )
        assert len(results) == 1
        assert results[0].metric_name == "Hallucination Rate"

    def test_empty_lists(self) -> None:
        assert compute_all_hallucination_metrics([], []) == []
