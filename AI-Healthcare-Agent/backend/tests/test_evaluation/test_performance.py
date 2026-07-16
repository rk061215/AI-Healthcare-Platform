from __future__ import annotations

from app.evaluation.performance import PerformanceAnalyzer, PerformanceMetric


class TestPerformanceAnalyzer:
    def test_analyze_empty(self) -> None:
        analyzer = PerformanceAnalyzer()
        report = analyzer.analyze()
        assert report.total_time_seconds == 0.0
        assert report.num_operations == 0
        assert report.error_count == 0

    def test_analyze_with_data(self) -> None:
        analyzer = PerformanceAnalyzer()
        with analyzer.tracker.measure("op1"):
            pass
        report = analyzer.analyze()
        assert report.num_operations > 0
        assert "op1" in report.operations

    def test_clear(self) -> None:
        analyzer = PerformanceAnalyzer()
        analyzer.tracker.record("op", 0.1)
        analyzer.clear()
        assert analyzer.analyze().num_operations == 0

    def test_error_count(self) -> None:
        analyzer = PerformanceAnalyzer()
        analyzer.tracker.record("op", 0.1, success=True)
        analyzer.tracker.record("op", 0.2, success=False)
        report = analyzer.analyze()
        assert report.error_count == 1


class TestPerformanceMetric:
    def test_evaluate(self) -> None:
        analyzer = PerformanceAnalyzer()
        analyzer.tracker.record("op", 0.1)
        metric = PerformanceMetric()
        result = metric.evaluate(analyzer=analyzer)
        assert result.metric_name == "Performance"
        assert result.details["num_operations"] > 0

    def test_evaluate_no_analyzer(self) -> None:
        metric = PerformanceMetric()
        result = metric.evaluate()
        assert result.passed is False
