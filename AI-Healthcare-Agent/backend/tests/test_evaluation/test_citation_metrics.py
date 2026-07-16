from __future__ import annotations

from app.evaluation.citation_metrics import (
    CitationCoverageMetric,
    CitationF1Metric,
    CitationPrecisionMetric,
    CitationRecallMetric,
    CitationRedundancyMetric,
    citation_coverage,
    citation_f1,
    citation_precision,
    citation_recall,
    citation_redundancy,
    compute_all_citation_metrics,
)


class TestCitationPrecision:
    def test_all_valid(self) -> None:
        assert citation_precision(
            ["source_a", "source_b"],
            ["source_a", "source_b", "source_c"],
        ) == 1.0

    def test_some_valid(self) -> None:
        assert citation_precision(
            ["source_a", "source_x"],
            ["source_a", "source_b"],
        ) == 0.5

    def test_empty_citations(self) -> None:
        assert citation_precision([], ["a"]) == 0.0

    def test_empty_sources(self) -> None:
        assert citation_precision(["a"], []) == 0.0


class TestCitationRecall:
    def test_all_found(self) -> None:
        assert citation_recall(
            ["source_a", "source_b", "source_c"],
            ["source_a", "source_c"],
        ) == 1.0

    def test_some_found(self) -> None:
        assert citation_recall(
            ["source_a"],
            ["source_a", "source_b"],
        ) == 0.5

    def test_empty_citations(self) -> None:
        assert citation_recall([], ["a"]) == 0.0

    def test_empty_sources(self) -> None:
        assert citation_recall(["a"], []) == 0.0


class TestCitationF1:
    def test_perfect_f1(self) -> None:
        f1 = citation_f1(["a", "b"], ["a", "b"])
        assert abs(f1 - 1.0) < 1e-10

    def test_no_overlap(self) -> None:
        assert citation_f1(["a"], ["b"]) == 0.0


class TestCitationCoverage:
    def test_full_coverage(self) -> None:
        assert citation_coverage(
            ["a", "b"],
            ["a", "b", "c"],
        ) == 2.0 / 3.0

    def test_no_coverage(self) -> None:
        assert citation_coverage(["x"], ["a", "b"]) == 0.0

    def test_empty_expected(self) -> None:
        assert citation_coverage(["a"], []) == 0.0


class TestCitationRedundancy:
    def test_no_redundancy(self) -> None:
        assert citation_redundancy(["a", "b", "c"]) == 0.0

    def test_all_duplicates(self) -> None:
        assert citation_redundancy(["a", "a", "a"]) == 1.0 - 1.0 / 3.0

    def test_empty(self) -> None:
        assert citation_redundancy([]) == 0.0


class TestCitationPrecisionMetric:
    def test_evaluate(self) -> None:
        metric = CitationPrecisionMetric()
        result = metric.evaluate(
            citations=["a", "b"],
            relevant_sources=["a", "c"],
        )
        assert result.metric_name == "Citation Precision"
        assert result.score == 0.5


class TestCitationRecallMetric:
    def test_evaluate(self) -> None:
        metric = CitationRecallMetric()
        result = metric.evaluate(
            citations=["a", "b"],
            relevant_sources=["a", "c"],
        )
        assert result.score == 0.5


class TestCitationF1Metric:
    def test_evaluate(self) -> None:
        metric = CitationF1Metric()
        result = metric.evaluate(
            citations=["a"],
            relevant_sources=["a"],
        )
        assert result.score == 1.0


class TestCitationCoverageMetric:
    def test_evaluate(self) -> None:
        metric = CitationCoverageMetric()
        result = metric.evaluate(
            citations=["a", "b"],
            expected_citations=["a", "c"],
        )
        assert result.score == 0.5


class TestCitationRedundancyMetric:
    def test_evaluate(self) -> None:
        metric = CitationRedundancyMetric()
        result = metric.evaluate(citations=["a", "a", "b"])
        assert result.score > 0


class TestComputeAllCitationMetrics:
    def test_basic_computation(self) -> None:
        results = compute_all_citation_metrics(
            all_citations=[["a", "b"]],
            all_relevant_sources=[["a", "c"]],
            all_expected_citations=[["a", "d"]],
        )
        assert len(results) == 5
        names = [r.metric_name for r in results]
        assert "Citation Precision" in names
        assert "Citation Recall" in names
        assert "Citation F1" in names
        assert "Citation Coverage" in names
        assert "Citation Redundancy" in names

    def test_empty_lists(self) -> None:
        assert compute_all_citation_metrics([], [], []) == []
