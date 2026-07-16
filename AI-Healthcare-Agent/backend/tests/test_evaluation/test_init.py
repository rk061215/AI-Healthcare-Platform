from __future__ import annotations

import app.evaluation
import app.evaluation.metrics
import app.evaluation.retrieval_metrics
import app.evaluation.rag_metrics
import app.evaluation.hallucination
import app.evaluation.citation_metrics
import app.evaluation.latency
import app.evaluation.performance
import app.evaluation.token_usage
import app.evaluation.dataset_loader
import app.evaluation.ground_truth
import app.evaluation.benchmark_runner
import app.evaluation.report_generator
import app.evaluation.config
import app.evaluation.exceptions


class TestEvaluationExports:
    def test_evaluation_module_imports(self) -> None:
        assert hasattr(app.evaluation, "EvaluationConfig")
        assert hasattr(app.evaluation, "BenchmarkRunner")
        assert hasattr(app.evaluation, "DatasetLoader")
        assert hasattr(app.evaluation, "GroundTruthSet")
        assert hasattr(app.evaluation, "GroundTruthValidator")
        assert hasattr(app.evaluation, "ReportGenerator")
        assert hasattr(app.evaluation, "MetricRegistry")
        assert hasattr(app.evaluation, "MetricResult")
        assert hasattr(app.evaluation, "LatencyTracker")
        assert hasattr(app.evaluation, "PerformanceAnalyzer")
        assert hasattr(app.evaluation, "TokenUsageTracker")
        assert hasattr(app.evaluation, "RecallAtK")
        assert hasattr(app.evaluation, "PrecisionAtK")
        assert hasattr(app.evaluation, "MRR")
        assert hasattr(app.evaluation, "NDCG")
        assert hasattr(app.evaluation, "GroundednessMetric")
        assert hasattr(app.evaluation, "CitationAccuracyMetric")
        assert hasattr(app.evaluation, "AnswerRelevanceMetric")
        assert hasattr(app.evaluation, "HallucinationRateMetric")
        assert hasattr(app.evaluation, "EvaluationError")
        assert hasattr(app.evaluation, "MetricError")
        assert hasattr(app.evaluation, "DatasetError")
        assert hasattr(app.evaluation, "BenchmarkError")
        assert hasattr(app.evaluation, "UnsupportedMetricError")

    def test_metric_functions_imported(self) -> None:
        assert hasattr(app.evaluation, "recall_at_k")
        assert hasattr(app.evaluation, "precision_at_k")
        assert hasattr(app.evaluation, "mean_reciprocal_rank")
        assert hasattr(app.evaluation, "ndcg_at_k")
        assert hasattr(app.evaluation, "groundedness")
        assert hasattr(app.evaluation, "citation_accuracy")
        assert hasattr(app.evaluation, "answer_relevance")
        assert hasattr(app.evaluation, "detect_hallucinated_claims")
        assert hasattr(app.evaluation, "hallucination_rate")
        assert hasattr(app.evaluation, "citation_precision")
        assert hasattr(app.evaluation, "citation_recall")
        assert hasattr(app.evaluation, "citation_f1")

    def test_all_exported(self) -> None:
        assert len(app.evaluation.__all__) > 50
        assert "EvaluationConfig" in app.evaluation.__all__
        assert "BenchmarkRunner" in app.evaluation.__all__
        assert "recall_at_k" in app.evaluation.__all__
