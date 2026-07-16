from __future__ import annotations

import time

from app.langgraph.graph_metrics import MetricsCollector


class TestMetricsCollector:
    def test_initial_state(self):
        mc = MetricsCollector(graph_name="test", session_id="sess_1")
        snap = mc.snapshot("completed")
        assert snap.graph_name == "test"
        assert snap.session_id == "sess_1"
        assert snap.node_count == 0
        assert snap.total_duration_ms > 0

    def test_node_timing(self):
        mc = MetricsCollector(graph_name="test", session_id="sess_1")
        mc.start_node("load_memory")
        time.sleep(0.01)
        mc.end_node("load_memory")
        snap = mc.snapshot("completed")
        assert snap.node_count == 1
        assert "load_memory" in snap.node_durations
        assert snap.node_durations["load_memory"] > 0

    def test_multiple_nodes(self):
        mc = MetricsCollector(graph_name="test", session_id="sess_1")
        for name in ["a", "b", "c"]:
            mc.start_node(name)
            mc.end_node(name)
        snap = mc.snapshot("completed")
        assert snap.node_count == 3

    def test_latency_recording(self):
        mc = MetricsCollector(graph_name="test", session_id="sess_1")
        mc.record_memory_latency(12.5)
        mc.record_retrieval_latency(45.2)
        mc.record_tool_latency(200.0)
        mc.record_generation_latency(350.0)
        snap = mc.snapshot("completed")
        assert snap.memory_latency_ms == 12.5
        assert snap.retrieval_latency_ms == 45.2
        assert snap.tool_latency_ms == 200.0
        assert snap.generation_latency_ms == 350.0

    def test_token_usage(self):
        mc = MetricsCollector(graph_name="test", session_id="sess_1")
        mc.record_token_usage({"prompt_tokens": 100, "completion_tokens": 50})
        mc.record_token_usage({"prompt_tokens": 200})
        snap = mc.snapshot("completed")
        assert snap.token_usage["prompt_tokens"] == 300
        assert snap.token_usage["completion_tokens"] == 50

    def test_error_count(self):
        mc = MetricsCollector(graph_name="test", session_id="sess_1")
        mc.increment_errors()
        mc.increment_errors()
        snap = mc.snapshot("completed")
        assert snap.error_count == 2

    def test_snapshot_to_dict(self):
        mc = MetricsCollector(graph_name="test", session_id="sess_1")
        snap = mc.snapshot("completed")
        d = snap.to_dict()
        assert d["graph_name"] == "test"
        assert d["session_id"] == "sess_1"
        assert d["status"] == "completed"
