from __future__ import annotations

import pytest

from app.evaluation.exceptions import (
    BenchmarkError,
    BenchmarkTimeoutError,
    ConfigurationError,
    DatasetError,
    DatasetNotFoundError,
    EvaluationError,
    GroundTruthError,
    LatencyError,
    MetricError,
    ReportError,
    TokenUsageError,
    UnsupportedMetricError,
)


class TestEvaluationExceptions:
    def test_evaluation_error_base(self) -> None:
        err = EvaluationError("base error")
        assert isinstance(err, Exception)
        assert str(err) == "base error"

    def test_configuration_error(self) -> None:
        err = ConfigurationError("bad config")
        assert isinstance(err, EvaluationError)
        assert "bad config" in str(err)

    def test_metric_error(self) -> None:
        err = MetricError("metric failed")
        assert isinstance(err, EvaluationError)

    def test_unsupported_metric_error(self) -> None:
        err = UnsupportedMetricError("unsupported")
        assert isinstance(err, MetricError)

    def test_dataset_error(self) -> None:
        err = DatasetError("dataset problem")
        assert isinstance(err, EvaluationError)

    def test_dataset_not_found_error(self) -> None:
        err = DatasetNotFoundError("not found")
        assert isinstance(err, DatasetError)

    def test_ground_truth_error(self) -> None:
        err = GroundTruthError("ground truth problem")
        assert isinstance(err, EvaluationError)

    def test_benchmark_error(self) -> None:
        err = BenchmarkError("benchmark failed")
        assert isinstance(err, EvaluationError)

    def test_benchmark_timeout_error(self) -> None:
        err = BenchmarkTimeoutError("timeout")
        assert isinstance(err, BenchmarkError)

    def test_latency_error(self) -> None:
        err = LatencyError("latency issue")
        assert isinstance(err, EvaluationError)

    def test_report_error(self) -> None:
        err = ReportError("report generation failed")
        assert isinstance(err, EvaluationError)

    def test_token_usage_error(self) -> None:
        err = TokenUsageError("token tracking error")
        assert isinstance(err, EvaluationError)

    def test_all_exceptions_raised(self) -> None:
        with pytest.raises(EvaluationError):
            raise ConfigurationError("test")
        with pytest.raises(EvaluationError):
            raise MetricError("test")
        with pytest.raises(EvaluationError):
            raise DatasetError("test")
        with pytest.raises(EvaluationError):
            raise BenchmarkError("test")
        with pytest.raises(EvaluationError):
            raise GroundTruthError("test")
