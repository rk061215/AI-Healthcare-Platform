from __future__ import annotations

import time
from typing import Any, Optional

from app.evaluation.citation_metrics import compute_all_citation_metrics
from app.evaluation.config import EvaluationConfig
from app.evaluation.dataset_loader import BenchmarkDataset, DatasetLoader
from app.evaluation.exceptions import BenchmarkError, BenchmarkTimeoutError
from app.evaluation.ground_truth import GroundTruthEntry, GroundTruthSet
from app.evaluation.hallucination import compute_all_hallucination_metrics
from app.evaluation.latency import LatencyTracker
from app.evaluation.metrics import MetricResult
from app.evaluation.models import BenchmarkResults, RunResults
from app.evaluation.performance import PerformanceAnalyzer, PerformanceMetric
from app.evaluation.rag_metrics import compute_all_rag_metrics
from app.evaluation.retrieval_metrics import compute_all_retrieval_metrics
from app.evaluation.report_generator import ReportGenerator
from app.evaluation.token_usage import TokenUsageMetric, TokenUsageTracker


class BenchmarkRunner:
    def __init__(
        self,
        config: Optional[EvaluationConfig] = None,
    ) -> None:
        self._config = config or EvaluationConfig()
        self._dataset_loader = DatasetLoader(self._config.dataset_path)
        self._latency_tracker = LatencyTracker()
        self._performance_analyzer = PerformanceAnalyzer()
        self._token_usage_tracker = TokenUsageTracker()
        self._report_generator = ReportGenerator()

    @property
    def config(self) -> EvaluationConfig:
        return self._config

    @property
    def latency_tracker(self) -> LatencyTracker:
        return self._latency_tracker

    @property
    def performance_analyzer(self) -> PerformanceAnalyzer:
        return self._performance_analyzer

    @property
    def token_usage_tracker(self) -> TokenUsageTracker:
        return self._token_usage_tracker

    def run_benchmark(
        self,
        dataset: Optional[BenchmarkDataset] = None,
        dataset_name: Optional[str] = None,
        dataset_category: Optional[str] = None,
    ) -> BenchmarkResults:
        if dataset is None and dataset_name is None:
            raise BenchmarkError("Either dataset or dataset_name must be provided")
        if dataset is None:
            dataset = self._dataset_loader.load_dataset(dataset_name, dataset_category)
        results = BenchmarkResults(
            benchmark_name=self._config.benchmark_name,
            benchmark_version=self._config.benchmark_version,
            dataset_name=dataset.name,
            num_samples=dataset.num_samples,
        )
        start_time = time.time()
        try:
            for run_idx in range(self._config.num_runs):
                if self._config.warmup_runs > 0 and run_idx < self._config.warmup_runs:
                    self._execute_warmup(dataset)
                    continue
                run_results = self._execute_run(dataset, run_idx)
                results.all_runs.append(run_results)
        except KeyboardInterrupt:
            raise BenchmarkError("Benchmark interrupted by user")
        total_duration = time.time() - start_time
        if total_duration > self._config.timeout_seconds:
            raise BenchmarkTimeoutError(
                f"Benchmark exceeded timeout of {self._config.timeout_seconds}s"
            )
        results.total_duration_seconds = total_duration
        if results.all_runs:
            valid_runs = [r for r in results.all_runs if r]
            if valid_runs:
                results.retrieval_results = self._aggregate_results(
                    [r.get("retrieval", []) for r in valid_runs]
                )
                results.rag_results = self._aggregate_results(
                    [r.get("rag", []) for r in valid_runs]
                )
                results.hallucination_results = self._aggregate_results(
                    [r.get("hallucination", []) for r in valid_runs]
                )
                results.citation_results = self._aggregate_results(
                    [r.get("citation", []) for r in valid_runs]
                )
                results.performance_results = self._aggregate_results(
                    [r.get("performance", []) for r in valid_runs]
                )
                results.token_usage_results = self._aggregate_results(
                    [r.get("token_usage", []) for r in valid_runs]
                )
        return results

    def generate_report(
        self,
        results: BenchmarkResults,
        output_path: Optional[str] = None,
    ) -> str:
        return self._report_generator.generate(
            results=results,
            config=self._config,
            output_path=output_path or self._config.output_path,
        )

    def _execute_warmup(self, dataset: BenchmarkDataset) -> None:
        if dataset.samples:
            sample = dataset.samples[0]
            _ = self._compute_retrieval_metrics_for_sample(sample)

    def _execute_run(
        self,
        dataset: BenchmarkDataset,
        run_idx: int,
    ) -> RunResults:
        run_results: RunResults = {}
        queries_retrieved: list[list[str]] = []
        queries_relevant: list[list[str]] = []
        queries_relevance: list[dict[str, float]] = []
        answers: list[str] = []
        questions: list[str] = []
        contexts: list[list[str]] = []
        relevant_chunks_list: list[list[str]] = []
        citations_list: list[list[dict[str, Any]]] = []
        all_raw_citations: list[list[str]] = []
        all_relevant_sources: list[list[str]] = []
        all_expected_citations: list[list[str]] = []
        for sample in dataset.samples:
            queries_retrieved.append(sample.retrieved_docs)
            queries_relevant.append(sample.relevant_docs)
            queries_relevance.append(sample.relevance_scores)
            answers.append(sample.expected_answer)
            questions.append(sample.query)
            contexts.append(sample.context_chunks)
            relevant_chunks_list.append(sample.relevant_chunks)
            citations_list.append(sample.citations)
            citation_texts = [c.get("text", "") if isinstance(c, dict) else str(c) for c in sample.citations]
            all_raw_citations.append(citation_texts)
            all_relevant_sources.append(sample.relevant_chunks)
            all_expected_citations.append(sample.expected_citations)
        if self._config.retrieval_metrics_enabled:
            run_results["retrieval"] = compute_all_retrieval_metrics(
                queries_retrieved=queries_retrieved,
                queries_relevant=queries_relevant,
                queries_relevance=queries_relevance,
                k_values=self._config.k_values,
            )
        if self._config.rag_metrics_enabled:
            run_results["rag"] = compute_all_rag_metrics(
                answers=answers,
                questions=questions,
                contexts=contexts,
                relevant_chunks_list=relevant_chunks_list,
                citations_list=citations_list,
            )
        if self._config.hallucination_metrics_enabled:
            run_results["hallucination"] = compute_all_hallucination_metrics(
                answers=answers,
                contexts=contexts,
            )
        if self._config.citation_metrics_enabled:
            run_results["citation"] = compute_all_citation_metrics(
                all_citations=all_raw_citations,
                all_relevant_sources=all_relevant_sources,
                all_expected_citations=all_expected_citations,
            )
        if self._config.performance_metrics_enabled:
            perf_metric = PerformanceMetric()
            run_results["performance"] = [perf_metric.evaluate(analyzer=self._performance_analyzer)]
        if self._config.token_usage_metrics_enabled:
            token_metric = TokenUsageMetric()
            run_results["token_usage"] = [token_metric.evaluate(tracker=self._token_usage_tracker)]
        return run_results

    def _compute_retrieval_metrics_for_sample(self, sample: BenchmarkSample) -> None:
        pass

    def _aggregate_results(
        self,
        run_results_list: list[list[MetricResult]],
    ) -> list[MetricResult]:
        if not run_results_list:
            return []
        metric_names = set()
        for results in run_results_list:
            for r in results:
                metric_names.add(r.metric_name)
        aggregated: list[MetricResult] = []
        for name in sorted(metric_names):
            scores = []
            details_list = []
            num_samples = 0
            for results in run_results_list:
                for r in results:
                    if r.metric_name == name:
                        scores.append(r.score)
                        details_list.append(r.details)
                        num_samples = max(num_samples, r.num_samples)
            if scores:
                avg_score = sum(scores) / len(scores)
                aggregated.append(MetricResult(
                    metric_name=name,
                    score=avg_score,
                    category=run_results_list[0][0].category if run_results_list[0] else "general",
                    details={
                        "mean": avg_score,
                        "min": min(scores),
                        "max": max(scores),
                        "num_runs": len(scores),
                        "per_run_details": details_list,
                    },
                    num_samples=num_samples,
                ))
        return aggregated

    def load_ground_truth(
        self,
        dataset_name: str,
        category: Optional[str] = None,
    ) -> GroundTruthSet:
        dataset = self._dataset_loader.load_dataset(dataset_name, category)
        entries = [
            GroundTruthEntry(
                query=s.query,
                expected_answer=s.expected_answer,
                expected_citations=s.expected_citations,
                expected_retrieved_docs=s.retrieved_docs,
                expected_relevance_scores=s.relevance_scores,
                expected_medications=s.expected_medications,
                expected_diagnoses=s.expected_diagnoses,
                expected_lab_results=s.expected_lab_results,
                expected_follow_ups=s.expected_follow_ups,
                metadata=s.metadata,
            )
            for s in dataset.samples
        ]
        return GroundTruthSet(name=dataset_name, entries=entries)
