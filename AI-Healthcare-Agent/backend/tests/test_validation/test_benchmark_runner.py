import pytest
from app.validation.benchmark.benchmark_runner import BenchmarkRunner
from app.validation.benchmark.benchmark_config import BenchmarkConfig
from app.validation.benchmark.benchmark_metrics import BenchmarkMetrics


class TestBenchmarkRunner:
    def _mock_answer_fn(self, question: str) -> dict:
        return {
            "answer": f"Answer to: {question}",
            "citations": ["doc_001:section"],
            "token_count": 100,
        }

    def _mock_ground_truth_fn(self, question: str) -> dict:
        return {
            "expected_answer": f"Expected: {question}",
            "expected_citations": ["doc_001:section"],
        }

    def test_run_basic(self):
        config = BenchmarkConfig(
            name="test_benchmark",
            num_benchmark_runs=1,
            measure_memory=False,
            save_history=False,
        )
        runner = BenchmarkRunner(config)
        questions = ["What is WBC?", "What is hemoglobin?"]
        result = runner.run(questions, self._mock_answer_fn)
        assert result.questions_attempted == 2
        assert result.questions_succeeded == 2
        assert result.overall_scores is not None

    def test_run_with_ground_truth(self):
        config = BenchmarkConfig(
            name="gt_benchmark",
            num_benchmark_runs=1,
            save_history=False,
        )
        runner = BenchmarkRunner(config)
        result = runner.run(["Q1?"], self._mock_answer_fn, self._mock_ground_truth_fn)
        assert result.questions_succeeded == 1

    def test_run_with_max_questions(self):
        config = BenchmarkConfig(
            name="max_test",
            max_questions=1,
            num_benchmark_runs=1,
            save_history=False,
        )
        runner = BenchmarkRunner(config)
        result = runner.run(["Q1?", "Q2?", "Q3?"], self._mock_answer_fn)
        assert result.questions_attempted == 1

    def test_run_handles_errors(self):
        def failing_fn(q):
            raise ValueError("test error")
        config = BenchmarkConfig(name="err_test", save_history=False)
        runner = BenchmarkRunner(config)
        result = runner.run(["Q1?"], failing_fn)
        assert result.questions_succeeded == 0
        assert len(result.errors) == 1

    def test_result_summary(self):
        config = BenchmarkConfig(name="summary_test", save_history=False)
        runner = BenchmarkRunner(config)
        result = runner.run(["Q1?"], self._mock_answer_fn)
        summary = result.summary()
        assert summary["config"] == "summary_test"
        assert summary["questions_attempted"] == 1
        assert summary["success_rate"] == 1.0

    def test_latency_measurement(self):
        import time
        def slow_fn(q):
            time.sleep(0.01)
            return {"answer": q}
        config = BenchmarkConfig(
            name="latency_test",
            num_benchmark_runs=1,
            save_history=False,
        )
        runner = BenchmarkRunner(config)
        result = runner.run(["Q1?"], slow_fn)
        assert result.latency_stats.get("min", 0) > 0

    def test_token_tracking(self):
        config = BenchmarkConfig(
            name="token_test",
            num_benchmark_runs=1,
            save_history=False,
        )
        runner = BenchmarkRunner(config)
        result = runner.run(["Q1?"], self._mock_answer_fn)
        assert result.token_stats.get("total", 0) > 0
