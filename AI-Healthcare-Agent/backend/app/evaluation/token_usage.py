from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.evaluation.metrics import Metric, MetricResult


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    operation: str = ""
    model: str = ""


@dataclass
class TokenUsageReport:
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    avg_prompt_tokens_per_query: float = 0.0
    avg_completion_tokens_per_query: float = 0.0
    avg_total_tokens_per_query: float = 0.0
    peak_prompt_tokens: int = 0
    peak_completion_tokens: int = 0
    peak_total_tokens: int = 0
    num_queries: int = 0
    per_operation: dict[str, dict[str, float]] = field(default_factory=dict)


class TokenUsageTracker:
    def __init__(self) -> None:
        self._usages: list[TokenUsage] = []

    def record(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        operation: str = "",
        model: str = "",
    ) -> None:
        usage = TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            operation=operation,
            model=model,
        )
        self._usages.append(usage)

    def get_usages(self, operation: Optional[str] = None) -> list[TokenUsage]:
        if operation is None:
            return list(self._usages)
        return [u for u in self._usages if u.operation == operation]

    def clear(self) -> None:
        self._usages.clear()

    def report(self) -> TokenUsageReport:
        if not self._usages:
            return TokenUsageReport()
        total_prompt = sum(u.prompt_tokens for u in self._usages)
        total_completion = sum(u.completion_tokens for u in self._usages)
        total = total_prompt + total_completion
        n = len(self._usages)
        per_op: dict[str, list[int]] = {}
        for u in self._usages:
            per_op.setdefault(u.operation, []).append(u.total_tokens)
        report = TokenUsageReport(
            total_prompt_tokens=total_prompt,
            total_completion_tokens=total_completion,
            total_tokens=total,
            avg_prompt_tokens_per_query=total_prompt / n if n else 0.0,
            avg_completion_tokens_per_query=total_completion / n if n else 0.0,
            avg_total_tokens_per_query=total / n if n else 0.0,
            peak_prompt_tokens=max(u.prompt_tokens for u in self._usages),
            peak_completion_tokens=max(u.completion_tokens for u in self._usages),
            peak_total_tokens=max(u.total_tokens for u in self._usages),
            num_queries=n,
            per_operation={
                op: {
                    "total": sum(tokens),
                    "avg": sum(tokens) / len(tokens),
                    "count": len(tokens),
                }
                for op, tokens in per_op.items()
            },
        )
        return report


class TokenUsageMetric(Metric):
    def __init__(self) -> None:
        super().__init__(name="Token Usage", category="token_usage")

    def evaluate(
        self,
        tracker: Optional[TokenUsageTracker] = None,
        **kwargs: Any,
    ) -> MetricResult:
        if tracker is None:
            return MetricResult(
                metric_name=self._name,
                score=0.0,
                category=self._category,
                details={"error": "No TokenUsageTracker provided"},
                passed=False,
            )
        report = tracker.report()
        return MetricResult(
            metric_name=self._name,
            score=report.total_tokens,
            category=self._category,
            details={
                "total_prompt_tokens": report.total_prompt_tokens,
                "total_completion_tokens": report.total_completion_tokens,
                "total_tokens": report.total_tokens,
                "avg_prompt_tokens_per_query": report.avg_prompt_tokens_per_query,
                "avg_completion_tokens_per_query": report.avg_completion_tokens_per_query,
                "avg_total_tokens_per_query": report.avg_total_tokens_per_query,
                "peak_prompt_tokens": report.peak_prompt_tokens,
                "peak_completion_tokens": report.peak_completion_tokens,
                "peak_total_tokens": report.peak_total_tokens,
                "num_queries": report.num_queries,
                "per_operation": report.per_operation,
            },
            num_samples=report.num_queries,
        )
