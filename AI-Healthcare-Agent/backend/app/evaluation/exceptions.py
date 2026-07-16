from __future__ import annotations


class EvaluationError(Exception):
    """Base exception for the evaluation module."""


class ConfigurationError(EvaluationError):
    """Invalid evaluation configuration."""


class MetricError(EvaluationError):
    """Error during metric calculation."""


class UnsupportedMetricError(MetricError):
    """Metric type not supported by the current configuration."""


class DatasetError(EvaluationError):
    """Error loading or processing evaluation datasets."""


class DatasetNotFoundError(DatasetError):
    """Requested dataset does not exist."""


class GroundTruthError(EvaluationError):
    """Error processing ground truth data."""


class BenchmarkError(EvaluationError):
    """Error during benchmark execution."""


class BenchmarkTimeoutError(BenchmarkError):
    """Benchmark execution exceeded timeout."""


class LatencyError(EvaluationError):
    """Error during latency measurement."""


class ReportError(EvaluationError):
    """Error generating evaluation report."""


class TokenUsageError(EvaluationError):
    """Error tracking token usage."""
