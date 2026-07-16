import pytest
from app.validation.benchmark.benchmark_suite import BenchmarkResult, BenchmarkSuite
from app.validation.benchmark.benchmark_config import BenchmarkConfig


class TestBenchmarkSuite:
    def test_add_and_aggregate(self):
        suite = BenchmarkSuite(BenchmarkConfig(name="test"))
        r1 = BenchmarkResult(
            config_name="test",
            questions_attempted=2,
            questions_succeeded=2,
            overall_scores={"recall_at_5": 0.8, "precision_at_5": 0.7},
            latency_stats={"mean": 100.0, "p95": 200.0},
            token_stats={"total": 500, "mean": 250},
        )
        r2 = BenchmarkResult(
            config_name="test",
            questions_attempted=2,
            questions_succeeded=2,
            overall_scores={"recall_at_5": 0.9, "precision_at_5": 0.8},
            latency_stats={"mean": 150.0, "p95": 300.0},
            token_stats={"total": 700, "mean": 350},
        )
        suite.add_result(r1)
        suite.add_result(r2)
        agg = suite.aggregate()
        assert agg is not None
        assert agg.overall_scores["recall_at_5"] == pytest.approx(0.85)
        assert agg.overall_scores["precision_at_5"] == pytest.approx(0.75)
        assert agg.questions_attempted == 4

    def test_empty_aggregate(self):
        suite = BenchmarkSuite(BenchmarkConfig(name="empty"))
        assert suite.aggregate() is None

    def test_single_result_aggregate(self):
        suite = BenchmarkSuite(BenchmarkConfig(name="single"))
        r = BenchmarkResult(config_name="single", questions_attempted=1, questions_succeeded=1)
        suite.add_result(r)
        agg = suite.aggregate()
        assert agg is not None
        assert agg.questions_attempted == 1

    def test_result_summary_keys(self):
        r = BenchmarkResult(
            config_name="test",
            questions_attempted=10,
            questions_succeeded=8,
            overall_scores={"recall": 0.8},
        )
        summary = r.summary()
        assert summary["success_rate"] == 0.8
        assert summary["error_count"] == 0
        assert "overall_scores" in summary

    def test_success_rate_zero(self):
        r = BenchmarkResult(config_name="test")
        assert r.success_rate() == 0.0

    def test_aggregate_with_memory(self):
        suite = BenchmarkSuite(BenchmarkConfig(name="mem_test"))
        r = BenchmarkResult(
            config_name="mem_test",
            questions_attempted=2,
            questions_succeeded=2,
            overall_scores={"recall": 0.8},
            memory_stats={"peak_mb": 256.0, "mean_mb": 128.0},
        )
        suite.add_result(r)
        agg = suite.aggregate()
        assert agg is not None
        assert agg.memory_stats["peak_mb"] == 256.0
