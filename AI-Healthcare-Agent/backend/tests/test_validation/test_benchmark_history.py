import tempfile
from pathlib import Path

import pytest
from app.validation.benchmark.benchmark_history import BenchmarkHistory
from app.validation.benchmark.benchmark_suite import BenchmarkResult


class TestBenchmarkHistory:
    @pytest.fixture
    def history(self):
        tmpdir = tempfile.mkdtemp()
        return BenchmarkHistory(storage_dir=tmpdir)

    def _make_result(self, name: str = "test_benchmark") -> BenchmarkResult:
        return BenchmarkResult(
            config_name=name,
            timestamp="20260716_120000",
            questions_attempted=5,
            questions_succeeded=4,
            overall_scores={"recall_at_5": 0.8},
        )

    def test_save_and_load(self, history):
        r = self._make_result()
        path = history.save_result(r)
        assert Path(path).exists()
        loaded = history.load_result(path)
        assert loaded is not None
        assert loaded.config_name == "test_benchmark"
        assert loaded.questions_attempted == 5

    def test_load_nonexistent(self, history):
        assert history.load_result("/nonexistent/path.json") is None

    def test_list_history(self, history):
        assert history.list_history() == []
        history.save_result(self._make_result())
        lst = history.list_history()
        assert len(lst) >= 1

    def test_get_latest(self, history):
        history.save_result(self._make_result("bench_v1"))
        latest = history.get_latest("bench_v1")
        assert latest is not None
        assert latest.config_name == "bench_v1"

    def test_get_latest_nonexistent(self, history):
        assert history.get_latest("nonexistent") is None

    def test_compare(self, history):
        r1 = BenchmarkResult(
            config_name="a",
            overall_scores={"recall": 0.7, "precision": 0.8},
        )
        r2 = BenchmarkResult(
            config_name="b",
            overall_scores={"recall": 0.9, "precision": 0.85},
        )
        comparison = history.compare(r1, r2)
        assert comparison["recall"]["baseline"] == 0.7
        assert comparison["recall"]["current"] == 0.9
        assert comparison["recall"]["regression"] is False
        assert abs(comparison["precision"]["diff"] - 0.05) < 0.001

    def test_compare_regression_detection(self, history):
        r1 = BenchmarkResult(config_name="a", overall_scores={"recall": 0.9})
        r2 = BenchmarkResult(config_name="b", overall_scores={"recall": 0.7})
        comparison = history.compare(r1, r2)
        assert comparison["recall"]["regression"] is True
