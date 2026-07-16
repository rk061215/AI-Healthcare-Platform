from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Optional

from app.evaluation.config import EvaluationConfig
from app.evaluation.metrics import MetricResult
from app.evaluation.models import BenchmarkResults


class ReportGenerator:
    def generate(
        self,
        results: BenchmarkResults,
        config: EvaluationConfig,
        output_path: str = "evaluation_reports",
    ) -> str:
        os.makedirs(output_path, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_name = f"{results.benchmark_name}_{timestamp}"
        data = self._build_report_data(results, config)
        report_path = os.path.join(output_path, f"{report_name}.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return report_path

    def generate_text(
        self,
        results: BenchmarkResults,
    ) -> str:
        lines: list[str] = []
        lines.append("=" * 70)
        lines.append(f"BENCHMARK REPORT: {results.benchmark_name}")
        lines.append(f"Version: {results.benchmark_version}")
        lines.append(f"Dataset: {results.dataset_name}")
        lines.append(f"Samples: {results.num_samples}")
        lines.append(f"Duration: {results.total_duration_seconds:.2f}s")
        lines.append(f"Runs: {results.num_runs}")
        lines.append("=" * 70)
        lines.append("")
        for category, category_results in [
            ("RETRIEVAL METRICS", results.retrieval_results),
            ("RAG METRICS", results.rag_results),
            ("HALLUCINATION METRICS", results.hallucination_results),
            ("CITATION METRICS", results.citation_results),
            ("PERFORMANCE METRICS", results.performance_results),
            ("TOKEN USAGE METRICS", results.token_usage_results),
        ]:
            if not category_results:
                continue
            lines.append(f"--- {category} ---")
            for metric in category_results:
                score_pct = metric.score * 100 if metric.score <= 1.0 else metric.score
                lines.append(f"  {metric.metric_name:40s} {score_pct:>8.2f}{'%' if metric.score <= 1.0 else ''}")
            lines.append("")
        if results.errors:
            lines.append("--- ERRORS ---")
            for error in results.errors:
                lines.append(f"  - {error}")
            lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    def _build_report_data(
        self,
        results: BenchmarkResults,
        config: EvaluationConfig,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "report": {
                "benchmark_name": results.benchmark_name,
                "benchmark_version": results.benchmark_version,
                "dataset_name": results.dataset_name,
                "num_samples": results.num_samples,
                "total_duration_seconds": results.total_duration_seconds,
                "num_runs": results.num_runs,
                "generated_at": datetime.utcnow().isoformat(),
            },
            "config": {
                "provider": config.provider,
                "model": config.model,
                "top_k": config.top_k,
                "k_values": list(config.k_values),
                "num_runs": config.num_runs,
            },
            "metrics": {},
        }
        for category, category_results in [
            ("retrieval", results.retrieval_results),
            ("rag", results.rag_results),
            ("hallucination", results.hallucination_results),
            ("citation", results.citation_results),
            ("performance", results.performance_results),
            ("token_usage", results.token_usage_results),
        ]:
            if category_results:
                data["metrics"][category] = [
                    self._metric_to_dict(m) for m in category_results
                ]
        if config.report_include_raw_data and results.all_runs:
            data["raw_runs"] = [
                {cat: [self._metric_to_dict(m) for m in metrics]
                 for cat, metrics in run.items()}
                for run in results.all_runs
            ]
        if results.errors:
            data["errors"] = results.errors
        return data

    def _metric_to_dict(self, metric: MetricResult) -> dict[str, Any]:
        return {
            "name": metric.metric_name,
            "score": metric.score,
            "category": metric.category,
            "details": metric.details,
            "num_samples": metric.num_samples,
            "passed": metric.passed,
        }
