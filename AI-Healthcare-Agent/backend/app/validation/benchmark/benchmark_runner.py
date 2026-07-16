from __future__ import annotations

import time
import tracemalloc
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from app.validation.benchmark.benchmark_config import BenchmarkConfig
from app.validation.benchmark.benchmark_history import BenchmarkHistory
from app.validation.benchmark.benchmark_metrics import BenchmarkMetrics
from app.validation.benchmark.benchmark_suite import BenchmarkResult, BenchmarkSuite


class BenchmarkRunner:
    def __init__(self, config: Optional[BenchmarkConfig] = None):
        self.config = config or BenchmarkConfig()
        self.metrics = BenchmarkMetrics()
        self.suite = BenchmarkSuite(self.config)
        self.history = BenchmarkHistory(self.config.output_dir)

    def run(
        self,
        questions: list[str],
        answer_fn: Callable[[str], dict[str, Any]],
        ground_truth_fn: Optional[Callable[[str], dict[str, Any]]] = None,
    ) -> BenchmarkResult:
        total = len(questions)
        if self.config.max_questions:
            total = min(total, self.config.max_questions)
            questions = questions[:total]

        per_question: list[dict[str, Any]] = []
        all_latencies: list[float] = []
        all_tokens: list[float] = []
        all_memories: list[float] = []
        succeeded = 0
        errors: list[str] = []

        for i, q in enumerate(questions):
            try:
                result = self._run_single(q, answer_fn, ground_truth_fn)
                per_question.append(result)
                if "latency_ms" in result:
                    all_latencies.append(result["latency_ms"])
                if "token_count" in result:
                    all_tokens.append(result["token_count"])
                if "memory_mb" in result:
                    all_memories.append(result["memory_mb"])
                succeeded += 1
            except Exception as e:
                errors.append(f"Q{i}: {e}")
                per_question.append({"question": q, "error": str(e)})

        overall = self._aggregate_scores(per_question)

        benchmark_result = BenchmarkResult(
            config_name=self.config.name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            overall_scores=overall,
            per_question_scores=per_question,
            latency_stats=self._compute_stats(all_latencies) if all_latencies else {},
            memory_stats=self._compute_stats(all_memories) if all_memories else {},
            token_stats={
                "mean": BenchmarkMetrics.mean(all_tokens) if all_tokens else 0,
                "total": sum(all_tokens) if all_tokens else 0,
                "min": min(all_tokens) if all_tokens else 0,
                "max": max(all_tokens) if all_tokens else 0,
            } if all_tokens else {},
            errors=errors,
            questions_attempted=total,
            questions_succeeded=succeeded,
        )

        self.suite.add_result(benchmark_result)

        if self.config.save_history:
            self.history.save_result(benchmark_result)

        return benchmark_result

    def _run_single(
        self,
        question: str,
        answer_fn: Callable[[str], dict[str, Any]],
        ground_truth_fn: Optional[Callable[[str], dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {"question": question}

        if self.config.measure_memory:
            tracemalloc.start()

        start = time.perf_counter()
        response = answer_fn(question)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if self.config.measure_memory:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            result["memory_mb"] = peak / (1024 * 1024)
            result["memory_current_mb"] = current / (1024 * 1024)

        if self.config.measure_latency:
            result["latency_ms"] = elapsed_ms

        answer_text = response.get("answer", response.get("text", ""))
        result["answer"] = answer_text
        result["raw_response"] = response

        if self.config.measure_tokens:
            token_count = response.get("token_count", len(answer_text.split()) * 1.3)
            result["token_count"] = int(token_count)

        citations = response.get("citations", response.get("sources", []))
        result["citations"] = citations

        if ground_truth_fn:
            gt = ground_truth_fn(question)
            result["ground_truth"] = gt
            result["citation_precision"] = self._score_citations(
                citations, gt.get("expected_citations", [])
            )
            result["citation_recall"] = self._score_citations(
                citations, gt.get("expected_citations", []), recall=True
            )

        return result

    def _aggregate_scores(self, results: list[dict[str, Any]]) -> dict[str, float]:
        scores: dict[str, list[float]] = {}
        for r in results:
            for key in ("citation_precision", "citation_recall", "latency_ms"):
                if key in r:
                    scores.setdefault(key, []).append(r[key])

        aggregated: dict[str, float] = {}
        for key, values in scores.items():
            aggregated[key] = BenchmarkMetrics.mean(values)

        precision_list = scores.get("citation_precision", [])
        recall_list = scores.get("citation_recall", [])
        if precision_list and recall_list:
            p = BenchmarkMetrics.mean(precision_list)
            r_val = BenchmarkMetrics.mean(recall_list)
            aggregated["citation_f1"] = BenchmarkMetrics.citation_f1(p, r_val)

        return aggregated

    def _score_citations(
        self,
        predicted: list[str],
        expected: list[str],
        recall: bool = False,
    ) -> float:
        if not predicted or not expected:
            return 0.0
        pred_set = set(predicted)
        exp_set = set(expected)
        overlap = pred_set & exp_set
        if recall:
            return len(overlap) / len(exp_set)
        return len(overlap) / len(pred_set)

    def _compute_stats(self, values: list[float]) -> dict[str, float]:
        return {
            "mean": BenchmarkMetrics.mean(values),
            "median": BenchmarkMetrics.median(values),
            "p95": BenchmarkMetrics.percentile(values, 95),
            "p99": BenchmarkMetrics.percentile(values, 99),
            "min": min(values),
            "max": max(values),
            "std_dev": BenchmarkMetrics.std_dev(values),
        }
