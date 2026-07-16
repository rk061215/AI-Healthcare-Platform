from __future__ import annotations

from app.evaluation.token_usage import TokenUsageMetric, TokenUsageTracker


class TestTokenUsageTracker:
    def test_record_and_get(self) -> None:
        tracker = TokenUsageTracker()
        tracker.record(prompt_tokens=100, completion_tokens=50, operation="rag")
        usages = tracker.get_usages()
        assert len(usages) == 1
        assert usages[0].prompt_tokens == 100
        assert usages[0].completion_tokens == 50
        assert usages[0].total_tokens == 150

    def test_get_usages_filter(self) -> None:
        tracker = TokenUsageTracker()
        tracker.record(10, 5, operation="op1")
        tracker.record(20, 10, operation="op2")
        assert len(tracker.get_usages("op1")) == 1
        assert len(tracker.get_usages("nonexistent")) == 0

    def test_clear(self) -> None:
        tracker = TokenUsageTracker()
        tracker.record(10, 5)
        tracker.clear()
        assert len(tracker.get_usages()) == 0

    def test_report_empty(self) -> None:
        tracker = TokenUsageTracker()
        report = tracker.report()
        assert report.num_queries == 0
        assert report.total_tokens == 0

    def test_report_with_data(self) -> None:
        tracker = TokenUsageTracker()
        tracker.record(100, 50, operation="rag")
        tracker.record(200, 100, operation="rag")
        report = tracker.report()
        assert report.num_queries == 2
        assert report.total_prompt_tokens == 300
        assert report.total_completion_tokens == 150
        assert report.total_tokens == 450
        assert report.avg_prompt_tokens_per_query == 150.0
        assert report.avg_completion_tokens_per_query == 75.0
        assert report.peak_prompt_tokens == 200
        assert report.peak_completion_tokens == 100
        assert "rag" in report.per_operation


class TestTokenUsageMetric:
    def test_evaluate(self) -> None:
        tracker = TokenUsageTracker()
        tracker.record(100, 50)
        metric = TokenUsageMetric()
        result = metric.evaluate(tracker=tracker)
        assert result.metric_name == "Token Usage"
        assert result.details["total_tokens"] == 150

    def test_evaluate_no_tracker(self) -> None:
        metric = TokenUsageMetric()
        result = metric.evaluate()
        assert result.passed is False
