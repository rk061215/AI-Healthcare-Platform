from __future__ import annotations

import time

from app.evaluation.latency import LatencyMetric, LatencyTracker


class TestLatencyTracker:
    def test_measure_context_manager(self) -> None:
        tracker = LatencyTracker()
        with tracker.measure("test_op"):
            time.sleep(0.01)
        measurements = tracker.get_measurements("test_op")
        assert len(measurements) == 1
        assert measurements[0].operation == "test_op"
        assert measurements[0].duration_seconds >= 0.01
        assert measurements[0].success is True

    def test_measure_multiple_operations(self) -> None:
        tracker = LatencyTracker()
        with tracker.measure("op1"):
            pass
        with tracker.measure("op2"):
            pass
        assert len(tracker.get_measurements()) == 2

    def test_record(self) -> None:
        tracker = LatencyTracker()
        tracker.record("manual_op", 0.5, details={"key": "value"})
        measurements = tracker.get_measurements("manual_op")
        assert len(measurements) == 1
        assert abs(measurements[0].duration_seconds - 0.5) < 0.1
        assert measurements[0].details == {"key": "value"}

    def test_get_measurements_filter(self) -> None:
        tracker = LatencyTracker()
        tracker.record("op_a", 0.1)
        tracker.record("op_b", 0.2)
        assert len(tracker.get_measurements("op_a")) == 1
        assert len(tracker.get_measurements("nonexistent")) == 0

    def test_clear(self) -> None:
        tracker = LatencyTracker()
        tracker.record("op", 0.1)
        tracker.clear()
        assert len(tracker.get_measurements()) == 0

    def test_summary(self) -> None:
        tracker = LatencyTracker()
        tracker.record("op", 0.1)
        tracker.record("op", 0.2)
        tracker.record("op", 0.3)
        summary = tracker.summary()
        assert "op" in summary
        assert summary["op"]["count"] == 3
        assert summary["op"]["min"] == 0.1
        assert summary["op"]["max"] == 0.3
        assert abs(summary["op"]["avg"] - 0.2) < 0.01

    def test_summary_empty(self) -> None:
        tracker = LatencyTracker()
        assert tracker.summary() == {}

    def test_summary_excludes_failures(self) -> None:
        tracker = LatencyTracker()
        tracker.record("good", 0.1, success=True)
        tracker.record("bad", 0.2, success=False)
        summary = tracker.summary()
        assert "good" in summary
        assert "bad" not in summary


class TestLatencyMetric:
    def test_evaluate(self) -> None:
        tracker = LatencyTracker()
        tracker.record("total", 0.5)
        metric = LatencyMetric(operation="total")
        result = metric.evaluate(tracker=tracker)
        assert result.metric_name == "Latency (total)"
        assert abs(result.score - 0.5) < 0.1
        assert result.details["count"] == 1

    def test_evaluate_no_tracker(self) -> None:
        metric = LatencyMetric()
        result = metric.evaluate()
        assert result.passed is False
        assert "error" in result.details

    def test_evaluate_no_measurements(self) -> None:
        tracker = LatencyTracker()
        metric = LatencyMetric(operation="nonexistent")
        result = metric.evaluate(tracker=tracker)
        assert result.passed is False
