import math

import pytest
from app.validation.benchmark.benchmark_metrics import BenchmarkMetrics


class TestBenchmarkMetrics:
    def test_retrieval_recall(self):
        assert BenchmarkMetrics.retrieval_recall(3, 5) == 0.6
        assert BenchmarkMetrics.retrieval_recall(0, 5) == 0.0
        assert BenchmarkMetrics.retrieval_recall(5, 0) == 0.0

    def test_precision_at_k(self):
        assert BenchmarkMetrics.precision_at_k(3, 5) == 0.6
        assert BenchmarkMetrics.precision_at_k(0, 5) == 0.0
        assert BenchmarkMetrics.precision_at_k(5, 0) == 0.0

    def test_mean_reciprocal_rank(self):
        assert BenchmarkMetrics.mean_reciprocal_rank([False, True, False], 5) == 0.5
        assert BenchmarkMetrics.mean_reciprocal_rank([True, False], 5) == 1.0
        assert BenchmarkMetrics.mean_reciprocal_rank([False, False], 5) == 0.0
        assert BenchmarkMetrics.mean_reciprocal_rank([False], 1) == 0.0

    def test_ndcg_at_k(self):
        rel = [3.0, 2.0, 1.0]
        ndcg = BenchmarkMetrics.ndcg_at_k(rel, 3)
        assert ndcg == pytest.approx(1.0, rel=1e-4)
        rel2 = [0.0, 3.0, 2.0]
        ndcg2 = BenchmarkMetrics.ndcg_at_k(rel2, 3)
        assert ndcg2 < 1.0
        assert ndcg2 > 0.0

    def test_ndcg_empty(self):
        assert BenchmarkMetrics.ndcg_at_k([], 5) == 0.0

    def test_citation_precision(self):
        assert BenchmarkMetrics.citation_precision(3, 5) == 0.6
        assert BenchmarkMetrics.citation_precision(0, 5) == 0.0
        assert BenchmarkMetrics.citation_precision(5, 0) == 0.0

    def test_citation_recall(self):
        assert BenchmarkMetrics.citation_recall(3, 5) == 0.6
        assert BenchmarkMetrics.citation_recall(0, 5) == 0.0

    def test_citation_f1(self):
        assert BenchmarkMetrics.citation_f1(1.0, 1.0) == 1.0
        assert BenchmarkMetrics.citation_f1(0.6, 0.6) == pytest.approx(0.6)
        assert BenchmarkMetrics.citation_f1(0.0, 0.0) == 0.0

    def test_groundedness(self):
        assert BenchmarkMetrics.groundedness(8, 10) == 0.8
        assert BenchmarkMetrics.groundedness(0, 10) == 0.0
        assert BenchmarkMetrics.groundedness(0, 0) == 1.0

    def test_hallucination_rate(self):
        assert BenchmarkMetrics.hallucination_rate(2, 10) == 0.2
        assert BenchmarkMetrics.hallucination_rate(0, 10) == 0.0
        assert BenchmarkMetrics.hallucination_rate(0, 0) == 0.0

    def test_answer_relevance(self):
        assert BenchmarkMetrics.answer_relevance(8, 10) == 0.8
        assert BenchmarkMetrics.answer_relevance(0, 10) == 0.0
        assert BenchmarkMetrics.answer_relevance(0, 0) == 0.0

    def test_mean_median(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        assert BenchmarkMetrics.mean(values) == 3.0
        assert BenchmarkMetrics.median(values) == 3.0
        assert BenchmarkMetrics.median([1.0, 2.0, 3.0]) == 2.0

    def test_percentile(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        assert BenchmarkMetrics.percentile(values, 50) == pytest.approx(5.5)
        assert BenchmarkMetrics.percentile(values, 0) == 1.0
        assert BenchmarkMetrics.percentile(values, 100) == 10.0

    def test_std_dev(self):
        values = [1.0, 1.0, 1.0]
        assert BenchmarkMetrics.std_dev(values) == 0.0
        values2 = [1.0, 2.0, 3.0]
        assert BenchmarkMetrics.std_dev(values2) == pytest.approx(1.0)

    def test_compute_all(self):
        relevance = [3.0, 2.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        metrics = BenchmarkMetrics.compute_all(relevance, k_values=[1, 3, 5])
        assert "precision_at_1" in metrics
        assert "recall_at_3" in metrics
        assert "mrr_at_5" in metrics
        assert "ndcg_at_3" in metrics
        assert "map_at_5" in metrics
        assert metrics["precision_at_1"] == 1.0

    def test_average_precision_at_k(self):
        assert BenchmarkMetrics.average_precision_at_k([True, True], 2) == 1.0
        assert BenchmarkMetrics.average_precision_at_k([False, True], 2) == 0.5
        assert BenchmarkMetrics.average_precision_at_k([False, False], 2) == 0.0
