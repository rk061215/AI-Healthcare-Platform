from __future__ import annotations

import pytest

from app.evaluation.benchmark_runner import BenchmarkRunner
from app.evaluation.config import EvaluationConfig
from app.evaluation.dataset_loader import BenchmarkDataset, BenchmarkSample
from app.evaluation.exceptions import BenchmarkError


class TestBenchmarkRunner:
    def test_run_benchmark_with_dataset(self) -> None:
        config = EvaluationConfig(
            retrieval_metrics_enabled=True,
            rag_metrics_enabled=True,
            hallucination_metrics_enabled=True,
            citation_metrics_enabled=True,
            performance_metrics_enabled=False,
            token_usage_metrics_enabled=False,
        )
        runner = BenchmarkRunner(config=config)
        dataset = BenchmarkDataset(
            name="test",
            category="test",
            samples=[
                BenchmarkSample(
                    query="What medication?",
                    expected_answer="Metformin",
                    context_chunks=["Patient takes metformin"],
                    relevant_chunks=["Patient takes metformin"],
                    citations=[{"text": "Patient takes metformin"}],
                    expected_citations=["Patient takes metformin"],
                    retrieved_docs=["doc1", "doc2"],
                    relevant_docs=["doc1"],
                    relevance_scores={"doc1": 0.9, "doc2": 0.0},
                ),
            ],
        )
        results = runner.run_benchmark(dataset=dataset)
        assert results.benchmark_name == "default_benchmark"
        assert results.num_samples == 1
        assert results.total_duration_seconds >= 0
        assert len(results.retrieval_results) > 0
        assert len(results.rag_results) > 0
        assert len(results.hallucination_results) > 0
        assert len(results.citation_results) > 0

    def test_run_benchmark_no_dataset(self) -> None:
        runner = BenchmarkRunner()
        with pytest.raises(BenchmarkError):
            runner.run_benchmark()

    def test_run_benchmark_multiple_runs(self) -> None:
        config = EvaluationConfig(num_runs=2)
        runner = BenchmarkRunner(config=config)
        dataset = BenchmarkDataset(
            name="multi",
            category="test",
            samples=[
                BenchmarkSample(
                    query="test",
                    expected_answer="answer",
                    retrieved_docs=["a"],
                    relevant_docs=["a"],
                ),
            ],
        )
        results = runner.run_benchmark(dataset=dataset)
        assert results.num_runs == 1  # only non-warmup runs counted
        assert len(results.all_runs) == 2
        assert len(results.retrieval_results) > 0

    def test_run_benchmark_with_warmup(self) -> None:
        config = EvaluationConfig(num_runs=2, warmup_runs=1)
        runner = BenchmarkRunner(config=config)
        dataset = BenchmarkDataset(
            name="warmup",
            category="test",
            samples=[
                BenchmarkSample(
                    query="test",
                    expected_answer="answer",
                    retrieved_docs=["a"],
                    relevant_docs=["a"],
                ),
            ],
        )
        results = runner.run_benchmark(dataset=dataset)
        assert results.num_runs == 1  # 2 runs - 1 warmup = 1 effective

    def test_generate_report(self, tmp_path) -> None:
        config = EvaluationConfig(output_path=str(tmp_path / "reports"))
        runner = BenchmarkRunner(config=config)
        dataset = BenchmarkDataset(
            name="report_test",
            category="test",
            samples=[
                BenchmarkSample(
                    query="test",
                    expected_answer="answer",
                    retrieved_docs=["a"],
                    relevant_docs=["a"],
                ),
            ],
        )
        results = runner.run_benchmark(dataset=dataset)
        report_path = runner.generate_report(results)
        assert report_path is not None
        import os
        assert os.path.isfile(report_path)
