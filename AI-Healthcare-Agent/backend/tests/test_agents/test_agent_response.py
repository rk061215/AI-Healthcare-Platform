from __future__ import annotations

from app.agents.agent_response import AgentResponse
from app.agents.agent_state import ExecutionStatus


class TestAgentResponse:
    def test_default_creation(self) -> None:
        response = AgentResponse(success=True)
        assert response.success is True
        assert response.answer == ""
        assert response.data is None
        assert response.status == ExecutionStatus.SUCCESS

    def test_ok_response(self) -> None:
        response = AgentResponse.ok(
            answer="Test answer",
            session_id="s1",
            trace_id="trace1",
            total_duration_ms=150.0,
            token_usage={"prompt": 100, "completion": 50},
            citations=[{"id": 1}],
            metadata={"key": "value"},
        )
        assert response.success is True
        assert response.answer == "Test answer"
        assert response.session_id == "s1"
        assert response.total_duration_ms == 150.0
        assert response.token_usage["prompt"] == 100

    def test_error_response(self) -> None:
        response = AgentResponse.error(
            error="Something failed",
            session_id="s1",
            trace_id="trace1",
            total_duration_ms=50.0,
        )
        assert response.success is False
        assert response.error == "Something failed"
        assert response.status == ExecutionStatus.FAILURE
        assert response.answer == ""

    def test_ok_defaults(self) -> None:
        response = AgentResponse.ok()
        assert response.success is True
        assert response.answer == ""
        assert response.token_usage == {}
        assert response.citations == []
        assert response.metadata == {}

    def test_error_defaults(self) -> None:
        response = AgentResponse.error("error")
        assert response.success is False
        assert response.error == "error"
        assert response.session_id == ""
        assert response.total_duration_ms == 0.0

    def test_metadata_mutable(self) -> None:
        response = AgentResponse.ok(metadata={"key": "val"})
        response.metadata["new_key"] = "new_val"
        assert response.metadata["new_key"] == "new_val"

    def test_data_field(self) -> None:
        response = AgentResponse.ok(data={"result": 42})
        assert response.data == {"result": 42}
