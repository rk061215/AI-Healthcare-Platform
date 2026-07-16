from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class RegressionThresholds:
    max_latency_ms: float = 5000.0
    min_retrieval_recall: float = 0.7
    max_hallucination_rate: float = 0.15
    min_citation_precision: float = 0.6
    min_citation_recall: float = 0.5
    min_groundedness: float = 0.8
    min_answer_relevance: float = 0.7
    max_token_usage: int = 4096


@dataclass
class RegressionCheck:
    name: str
    passed: bool = False
    actual: float = 0.0
    threshold: float = 0.0
    message: str = ""


@dataclass
class RegressionResult:
    suite_name: str = ""
    passed: bool = False
    checks: list[RegressionCheck] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        total = len(self.checks)
        passed_checks = sum(1 for c in self.checks if c.passed)
        return {
            "suite_name": self.suite_name,
            "passed": self.passed,
            "checks_total": total,
            "checks_passed": passed_checks,
            "checks_failed": total - passed_checks,
            "errors": len(self.errors),
        }


class RegressionSuite:
    def __init__(self, thresholds: Optional[RegressionThresholds] = None):
        self.thresholds = thresholds or RegressionThresholds()
        self._history: list[RegressionResult] = []

    def run(
        self,
        benchmark_result: Any,
        answer_fn: Optional[Callable] = None,
    ) -> RegressionResult:
        result = RegressionResult(suite_name="clinical_regression")
        overall_scores = getattr(benchmark_result, "overall_scores", {})
        latency_stats = getattr(benchmark_result, "latency_stats", {})
        token_stats = getattr(benchmark_result, "token_stats", {})

        checks = [
            RegressionCheck(
                name="latency",
                actual=latency_stats.get("p95", 0),
                threshold=self.thresholds.max_latency_ms,
            ),
            RegressionCheck(
                name="retrieval_recall",
                actual=overall_scores.get("recall_at_5", 0),
                threshold=self.thresholds.min_retrieval_recall,
            ),
            RegressionCheck(
                name="hallucination_rate",
                actual=overall_scores.get("hallucination_rate", 0),
                threshold=self.thresholds.max_hallucination_rate,
            ),
            RegressionCheck(
                name="citation_precision",
                actual=overall_scores.get("citation_precision", 0),
                threshold=self.thresholds.min_citation_precision,
            ),
            RegressionCheck(
                name="citation_recall",
                actual=overall_scores.get("citation_recall", 0),
                threshold=self.thresholds.min_citation_recall,
            ),
            RegressionCheck(
                name="groundedness",
                actual=overall_scores.get("groundedness", 0),
                threshold=self.thresholds.min_groundedness,
            ),
            RegressionCheck(
                name="answer_relevance",
                actual=overall_scores.get("answer_relevance", 0),
                threshold=self.thresholds.min_answer_relevance,
            ),
            RegressionCheck(
                name="token_usage",
                actual=float(token_stats.get("mean", 0)),
                threshold=float(self.thresholds.max_token_usage),
            ),
        ]

        for check in checks:
            if check.name in ("hallucination_rate", "latency", "token_usage"):
                check.passed = check.actual <= check.threshold
                check.message = (
                    f"{check.name}: {check.actual:.3f} <= {check.threshold:.3f}"
                    if check.passed
                    else f"{check.name}: {check.actual:.3f} > {check.threshold:.3f} (FAIL)"
                )
            else:
                check.passed = check.actual >= check.threshold
                check.message = (
                    f"{check.name}: {check.actual:.3f} >= {check.threshold:.3f}"
                    if check.passed
                    else f"{check.name}: {check.actual:.3f} < {check.threshold:.3f} (FAIL)"
                )

        result.checks = checks
        result.passed = all(c.passed for c in checks)
        self._history.append(result)
        return result

    @property
    def history(self) -> list[RegressionResult]:
        return list(self._history)

    def compare_with_baseline(
        self, current: RegressionResult, baseline: RegressionResult,
    ) -> dict[str, Any]:
        comparison: dict[str, Any] = {}
        current_map = {c.name: c for c in current.checks}
        baseline_map = {c.name: c for c in baseline.checks}
        for name, cur in current_map.items():
            base = baseline_map.get(name)
            if base is not None:
                comparison[name] = {
                    "baseline": base.actual,
                    "current": cur.actual,
                    "regression": (
                        cur.actual < base.actual
                        if name not in ("hallucination_rate", "latency", "token_usage")
                        else cur.actual > base.actual
                    ),
                }
        return comparison
