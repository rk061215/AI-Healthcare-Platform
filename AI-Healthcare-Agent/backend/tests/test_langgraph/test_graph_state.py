from __future__ import annotations

from app.langgraph.graph_state import GraphPhase, GraphState, GraphStatus, NodeMetricsEntry


class TestGraphState:
    def test_default_state_creation(self):
        state = GraphState(graph_name="test_graph")
        assert state.graph_name == "test_graph"
        assert state.phase == GraphPhase.START.value
        assert state.status == GraphStatus.PENDING.value
        assert state.query == ""
        assert state.final_response == ""

    def test_state_with_query(self):
        state = GraphState(query="What is diabetes?", session_id="sess_1")
        assert state.query == "What is diabetes?"
        assert state.session_id == "sess_1"

    def test_to_dict_contains_core_fields(self):
        state = GraphState(query="test", session_id="sess_1")
        d = state.to_dict()
        assert d["query"] == "test"
        assert d["session_id"] == "sess_1"
        assert d["phase"] == GraphPhase.START.value
        assert d["status"] == GraphStatus.PENDING.value

    def test_snapshot_contains_all_public_attrs(self):
        state = GraphState(query="test", final_response="answer")
        snap = state.snapshot()
        assert snap["query"] == "test"
        assert snap["final_response"] == "answer"
        assert "phase" in snap
        assert "status" in snap

    def test_node_metrics_entry(self):
        entry = NodeMetricsEntry(
            node_name="load_memory",
            phase="memory_load",
            duration_ms=10.5,
            status="completed",
        )
        assert entry.node_name == "load_memory"
        assert entry.duration_ms == 10.5

    def test_state_tracks_errors(self):
        state = GraphState()
        state.errors.append("error 1")
        state.errors.append("error 2")
        assert len(state.errors) == 2

    def test_state_tracks_token_usage(self):
        state = GraphState()
        state.token_usage["prompt_tokens"] = 100
        state.token_usage["completion_tokens"] = 50
        assert state.token_usage["prompt_tokens"] == 100
        assert state.token_usage["completion_tokens"] == 50

    def test_needs_tool_defaults(self):
        state = GraphState()
        assert state.need_tool is False
        assert state.need_retrieval is True

    def test_services_dict(self):
        state = GraphState()
        state.services["memory_service"] = "mock"
        assert state.services["memory_service"] == "mock"

    def test_phase_transition(self):
        state = GraphState()
        state.phase = GraphPhase.MEMORY_LOAD.value
        assert state.phase == "memory_load"
        state.phase = GraphPhase.QA_GENERATION.value
        assert state.phase == "qa_generation"
        state.phase = GraphPhase.COMPLETED.value
        assert state.phase == "completed"
