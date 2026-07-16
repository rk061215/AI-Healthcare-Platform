from __future__ import annotations

from app.agents.agent_state import AgentPhase, AgentState, ExecutionStatus


class TestAgentPhase:
    def test_enum_values(self) -> None:
        assert AgentPhase.IDLE.value == "idle"
        assert AgentPhase.INITIALIZING.value == "initializing"
        assert AgentPhase.COMPLETED.value == "completed"
        assert AgentPhase.FAILED.value == "failed"


class TestExecutionStatus:
    def test_enum_values(self) -> None:
        assert ExecutionStatus.PENDING.value == "pending"
        assert ExecutionStatus.RUNNING.value == "running"
        assert ExecutionStatus.SUCCESS.value == "success"


class TestAgentState:
    def test_initial_state(self) -> None:
        state = AgentState(session_id="s1")
        assert state.session_id == "s1"
        assert state.phase == AgentPhase.IDLE
        assert state.status == ExecutionStatus.PENDING
        assert state.errors == []
        assert state.invoked_components == []
        assert state.retry_count == 0

    def test_start(self) -> None:
        state = AgentState(session_id="s1")
        state.start("trace123")
        assert state.trace_id == "trace123"
        assert state.phase == AgentPhase.INITIALIZING
        assert state.status == ExecutionStatus.RUNNING
        assert state.start_time > 0

    def test_complete(self) -> None:
        state = AgentState(session_id="s1")
        state.start("trace1")
        state.complete()
        assert state.phase == AgentPhase.COMPLETED
        assert state.status == ExecutionStatus.SUCCESS
        assert state.end_time > 0
        assert state.total_duration_ms > 0

    def test_fail(self) -> None:
        state = AgentState(session_id="s1")
        state.start("trace1")
        state.fail("Something went wrong")
        assert state.phase == AgentPhase.FAILED
        assert state.status == ExecutionStatus.FAILURE
        assert len(state.errors) == 1
        assert state.errors[0] == "Something went wrong"

    def test_add_component_trace(self) -> None:
        state = AgentState(session_id="s1")
        state.add_component_trace("rag", ExecutionStatus.SUCCESS, duration_ms=100.0)
        assert len(state.invoked_components) == 1
        assert state.invoked_components[0].component == "rag"
        assert state.invoked_components[0].duration_ms == 100.0

    def test_add_error(self) -> None:
        state = AgentState(session_id="s1")
        state.add_error("error 1")
        state.add_error("error 2")
        assert len(state.errors) == 2

    def test_set_phase(self) -> None:
        state = AgentState(session_id="s1")
        state.set_phase(AgentPhase.RETRIEVING_DOCUMENTS)
        assert state.phase == AgentPhase.RETRIEVING_DOCUMENTS

    def test_increment_retry(self) -> None:
        state = AgentState(session_id="s1")
        assert state.increment_retry() == 1
        assert state.increment_retry() == 2
        assert state.retry_count == 2

    def test_phase_sequence(self) -> None:
        state = AgentState(session_id="s1")
        state.start("trace1")
        assert state.phase == AgentPhase.INITIALIZING
        state.set_phase(AgentPhase.INVOKING_RAG)
        assert state.phase == AgentPhase.INVOKING_RAG
        state.complete()
        assert state.phase == AgentPhase.COMPLETED
