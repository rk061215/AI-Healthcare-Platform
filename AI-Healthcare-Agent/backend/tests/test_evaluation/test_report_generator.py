from __future__ import annotations

import json
import os

from app.evaluation.models import BenchmarkResults
from app.evaluation.config import EvaluationConfig
from app.evaluation.metrics import MetricResult
from app.evaluation.report_generator import ReportGenerator


class TestReportGenerator:
    def test_generate(self, tmp_path) -> None:
        results = BenchmarkResults(
            benchmark_name="test_benchmark",
            benchmark_version="1.0.0",
            dataset_name="test_dataset",
            num_samples=5,
            retrieval_results=[
                MetricResult(metric_name="Recall@5", score=0.8, category="retrieval"),
                MetricResult(metric_name="Precision@5", score=0.6, category="retrieval"),
            ],
            rag_results=[
                MetricResult(metric_name="Groundedness", score=0.9, category="rag"),
            ],
            total_duration_seconds=10.5,
        )
        config = EvaluationConfig(benchmark_name="test_benchmark")
        output_path = str(tmp_path / "reports")
        generator = ReportGenerator()
        report_path = generator.generate(results, config, output_path=output_path)
        assert os.path.isfile(report_path)
        with open(report_path, "r") as f:
            data = json.load(f)
        assert data["report"]["benchmark_name"] == "test_benchmark"
        assert data["report"]["dataset_name"] == "test_dataset"
        assert data["report"]["num_samples"] == 5
        assert data["report"]["total_duration_seconds"] == 10.5
        assert "retrieval" in data["metrics"]
        assert "rag" in data["metrics"]
        assert len(data["metrics"]["retrieval"]) == 2

    def test_generate_text(self) -> None:
        results = BenchmarkResults(
            benchmark_name="text_test",
            benchmark_version="1.0.0",
            dataset_name="ds",
            num_samples=3,
            retrieval_results=[
                MetricResult(metric_name="Recall@5", score=0.75, category="retrieval"),
            ],
            total_duration_seconds=5.0,
        )
        generator = ReportGenerator()
        text = generator.generate_text(results)
        assert "BENCHMARK REPORT" in text
        assert "text_test" in text
        assert "Recall@5" in text
        assert "75.00%" in text or "75" in text

    def test_generate_with_raw_data(self, tmp_path) -> None:
        results = BenchmarkResults(
            benchmark_name="raw_test",
            benchmark_version="1.0.0",
            dataset_name="ds",
            num_samples=1,
            retrieval_results=[MetricResult(metric_name="Recall@1", score=1.0, category="retrieval")],
            all_runs=[
                {"retrieval": [MetricResult(metric_name="Recall@1", score=1.0, category="retrieval")]},
            ],
            total_duration_seconds=1.0,
        )
        config = EvaluationConfig(
            benchmark_name="raw_test",
            report_include_raw_data=True,
        )
        output_path = str(tmp_path / "raw_reports")
        generator = ReportGenerator()
        report_path = generator.generate(results, config, output_path=output_path)
        with open(report_path, "r") as f:
            data = json.load(f)
        assert "raw_runs" in data
        assert len(data["raw_runs"]) == 1
