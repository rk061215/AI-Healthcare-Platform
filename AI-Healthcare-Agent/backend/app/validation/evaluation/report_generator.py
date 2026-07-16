from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.validation.evaluation.clinical_test_runner import (
    ClinicalTestResult,
    ClinicalTestSummary,
)
from app.validation.evaluation.regression_suite import RegressionResult


class ReportGenerator:
    @staticmethod
    def generate_validation_report(
        validation_results: dict[str, Any],
        output_path: Optional[str | Path] = None,
    ) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        report = f"""# Clinical Validation Report

> Generated: {ts}

## Overview

| Metric | Value |
|--------|-------|
| Datasets Validated | {validation_results.get('datasets_validated', 0)} |
| Total Entries | {validation_results.get('total_entries', 0)} |
| Errors | {validation_results.get('error_count', 0)} |
| Warnings | {validation_results.get('warning_count', 0)} |
| Valid | {validation_results.get('is_valid', False)} |

## Dataset Details

"""
        for ds in validation_results.get("datasets", []):
            report += f"""### {ds.get('name', 'unnamed')}
- Version: {ds.get('version', 'N/A')}
- Documents: {ds.get('documents', 0)}
- Entries: {ds.get('entries', 0)}
- Valid: {ds.get('valid', False)}
- Errors: {ds.get('error_count', 0)}
- Warnings: {ds.get('warning_count', 0)}

"""
        if validation_results.get("errors"):
            report += "## Errors\n\n"
            for err in validation_results["errors"]:
                report += f"- {err}\n"

        if validation_results.get("recommendations"):
            report += "\n## Recommendations\n\n"
            for rec in validation_results["recommendations"]:
                report += f"- {rec}\n"

        return ReportGenerator._write(report, output_path, "VALIDATION_REPORT")

    @staticmethod
    def generate_benchmark_report(
        benchmark_results: dict[str, Any],
        output_path: Optional[str | Path] = None,
    ) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        scores = benchmark_results.get("overall_scores", {})
        latency = benchmark_results.get("latency_stats", {})
        memory = benchmark_results.get("memory_stats", {})
        tokens = benchmark_results.get("token_stats", {})

        report = f"""# Benchmark Summary

> Generated: {ts}
> Config: {benchmark_results.get('config_name', 'N/A')}

## Results

| Metric | Value |
|--------|-------|
| Questions Attempted | {benchmark_results.get('questions_attempted', 0)} |
| Questions Succeeded | {benchmark_results.get('questions_succeeded', 0)} |
| Success Rate | {benchmark_results.get('questions_succeeded', 0) / max(benchmark_results.get('questions_attempted', 1), 1):.1%} |

## Retrieval Accuracy

| Metric | Value |
|--------|-------|
"""
        for key in sorted(scores.keys()):
            report += f"| {key} | {scores[key]:.4f} |\n"

        if latency:
            report += f"""
## Latency

| Metric | Value |
|--------|-------|
| Mean | {latency.get('mean', 0):.1f} ms |
| Median | {latency.get('median', 0):.1f} ms |
| P95 | {latency.get('p95', 0):.1f} ms |
| P99 | {latency.get('p99', 0):.1f} ms |
| Min | {latency.get('min', 0):.1f} ms |
| Max | {latency.get('max', 0):.1f} ms |
"""
        if memory:
            report += f"""
## Memory

| Metric | Value |
|--------|-------|
| Mean | {memory.get('mean_mb', 0):.1f} MB |
| Peak | {memory.get('peak_mb', 0):.1f} MB |
"""
        if tokens:
            report += f"""
## Token Usage

| Metric | Value |
|--------|-------|
| Mean | {tokens.get('mean', 0):.0f} |
| Total | {tokens.get('total', 0):.0f} |
"""

        if benchmark_results.get("errors"):
            report += "\n## Errors\n\n"
            for err in benchmark_results["errors"][:20]:
                report += f"- {err}\n"

        return ReportGenerator._write(report, output_path, "BENCHMARK_SUMMARY")

    @staticmethod
    def generate_regression_report(
        regression_result: RegressionResult,
        output_path: Optional[str | Path] = None,
    ) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        summary = regression_result.summary()
        report = f"""# Clinical Regression Report

> Generated: {ts}

## Overview

| Metric | Value |
|--------|-------|
| Suite | {regression_result.suite_name} |
| Overall | {"✅ PASSED" if regression_result.passed else "❌ FAILED"} |
| Checks Total | {summary['checks_total']} |
| Checks Passed | {summary['checks_passed']} |
| Checks Failed | {summary['checks_failed']} |

## Detailed Checks

| Check | Passed | Actual | Threshold |
|-------|--------|--------|-----------|
"""
        for check in regression_result.checks:
            icon = "✅" if check.passed else "❌"
            report += f"| {check.name} | {icon} | {check.actual:.3f} | {check.threshold:.3f} |\n"

        if regression_result.errors:
            report += "\n## Errors\n\n"
            for err in regression_result.errors:
                report += f"- {err}\n"

        return ReportGenerator._write(report, output_path, "REGRESSION_REPORT")

    @staticmethod
    def generate_optimization_report(
        optimization_results: dict[str, Any],
        output_path: Optional[str | Path] = None,
    ) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        report = f"""# Optimization Report

> Generated: {ts}

## Chunk Optimization

{ReportGenerator._fmt_opt_section(optimization_results.get('chunk', {}))}

## Retrieval Optimization

{ReportGenerator._fmt_opt_section(optimization_results.get('retrieval', {}))}

## Prompt Optimization

{ReportGenerator._fmt_opt_section(optimization_results.get('prompt', {}))}

## Reranking Optimization

{ReportGenerator._fmt_opt_section(optimization_results.get('reranking', {}))}

"""
        return ReportGenerator._write(report, output_path, "OPTIMIZATION_REPORT")

    @staticmethod
    def generate_performance_dashboard(
        data: dict[str, Any],
        output_path: Optional[str | Path] = None,
    ) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        dashboard = {
            "generated_at": ts,
            "version": "1.0.0",
            "system": data.get("system", {}),
            "benchmark": data.get("benchmark", {}),
            "validation": data.get("validation", {}),
            "regression": data.get("regression", {}),
            "optimization": data.get("optimization", {}),
            "recommendations": data.get("recommendations", []),
            "production_readiness_score": data.get("production_readiness_score", 0),
        }
        path = Path(output_path) if output_path else Path("PERFORMANCE_DASHBOARD.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(dashboard, f, indent=2, default=str)
        return str(path)

    @staticmethod
    def _fmt_opt_section(data: dict[str, Any]) -> str:
        if not data:
            return "No data available.\n"
        lines = [f"- Trials: {data.get('trials', 0)}"]
        best = data.get("best")
        if best:
            lines.append(f"- Best config: {best}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _write(content: str, path: Optional[str | Path], default_name: str) -> str:
        if path:
            output = Path(path)
        else:
            output = Path(f"{default_name}.md")
        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        return str(output)
