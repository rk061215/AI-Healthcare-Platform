"""AI Evaluation & Benchmarking module.

Provides a comprehensive framework for measuring quality, correctness, performance,
and robustness of AI system components. Supports retrieval metrics, RAG metrics,
hallucination detection, citation quality analysis, performance profiling, and
token usage tracking.

Usage:
    from app.evaluation import BenchmarkRunner, EvaluationConfig
    from app.evaluation.metrics import MetricRegistry, get_global_registry
    from app.evaluation.retrieval_metrics import recall_at_k, precision_at_k
    from app.evaluation.rag_metrics import groundedness, citation_accuracy
"""

from app.evaluation.benchmark_runner import BenchmarkRunner
from app.evaluation.models import BenchmarkResults
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
)
from app.evaluation.config import EvaluationConfig
from app.evaluation.dataset_loader import BenchmarkDataset, BenchmarkSample, DatasetLoader
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
from app.evaluation.ground_truth import GroundTruthEntry, GroundTruthSet, GroundTruthValidator
from app.evaluation.hallucination import (
    HallucinationRateMetric,
    contains_hallucination_patterns,
    contains_unsupported_medical_claims,
    detect_hallucinated_claims,
    hallucination_rate,
)
from app.evaluation.latency import LatencyMetric, LatencyMeasurement, LatencyTracker
from app.evaluation.metrics import Metric, MetricRegistry, MetricResult, get_global_registry, register_metric
from app.evaluation.performance import PerformanceAnalyzer, PerformanceMetric, PerformanceReport
from app.evaluation.rag_metrics import (
    AnswerRelevanceMetric,
    CitationAccuracyMetric,
    ContextPrecisionMetric,
    ContextRecallMetric,
    DiagnosisAccuracyMetric,
    FollowUpAccuracyMetric,
    GroundednessMetric,
    LabResultAccuracyMetric,
    MedicationAccuracyMetric,
    answer_relevance,
    citation_accuracy,
    context_precision,
    context_recall,
    groundedness,
    medication_extraction_accuracy,
    diagnosis_accuracy,
    lab_result_accuracy,
    follow_up_extraction_accuracy,
)
from app.evaluation.report_generator import ReportGenerator
from app.evaluation.retrieval_metrics import (
    MRR,
    NDCG,
    PrecisionAtK,
    RecallAtK,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from app.evaluation.token_usage import TokenUsageMetric, TokenUsageTracker, TokenUsageReport

__all__ = [
    "EvaluationConfig",
    "BenchmarkRunner",
    "BenchmarkResults",
    "BenchmarkDataset",
    "BenchmarkSample",
    "DatasetLoader",
    "GroundTruthEntry",
    "GroundTruthSet",
    "GroundTruthValidator",
    "ReportGenerator",
    "Metric",
    "MetricResult",
    "MetricRegistry",
    "get_global_registry",
    "register_metric",
    "RecallAtK",
    "PrecisionAtK",
    "MRR",
    "NDCG",
    "recall_at_k",
    "precision_at_k",
    "mean_reciprocal_rank",
    "ndcg_at_k",
    "GroundednessMetric",
    "CitationAccuracyMetric",
    "ContextPrecisionMetric",
    "ContextRecallMetric",
    "AnswerRelevanceMetric",
    "MedicationAccuracyMetric",
    "DiagnosisAccuracyMetric",
    "LabResultAccuracyMetric",
    "FollowUpAccuracyMetric",
    "groundedness",
    "citation_accuracy",
    "context_precision",
    "context_recall",
    "answer_relevance",
    "medication_extraction_accuracy",
    "diagnosis_accuracy",
    "lab_result_accuracy",
    "follow_up_extraction_accuracy",
    "HallucinationRateMetric",
    "detect_hallucinated_claims",
    "hallucination_rate",
    "contains_hallucination_patterns",
    "contains_unsupported_medical_claims",
    "CitationPrecisionMetric",
    "CitationRecallMetric",
    "CitationF1Metric",
    "CitationCoverageMetric",
    "CitationRedundancyMetric",
    "citation_precision",
    "citation_recall",
    "citation_f1",
    "citation_coverage",
    "citation_redundancy",
    "LatencyTracker",
    "LatencyMeasurement",
    "LatencyMetric",
    "PerformanceAnalyzer",
    "PerformanceMetric",
    "PerformanceReport",
    "TokenUsageTracker",
    "TokenUsageReport",
    "TokenUsageMetric",
    "EvaluationError",
    "ConfigurationError",
    "MetricError",
    "UnsupportedMetricError",
    "DatasetError",
    "DatasetNotFoundError",
    "GroundTruthError",
    "BenchmarkError",
    "BenchmarkTimeoutError",
    "LatencyError",
    "ReportError",
    "TokenUsageError",
]
