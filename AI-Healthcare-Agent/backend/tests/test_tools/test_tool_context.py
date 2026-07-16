from __future__ import annotations

from app.tools.tool_context import ToolContext


class TestToolContext:
    def test_default_creation(self):
        ctx = ToolContext(tool_name="test")
        assert ctx.tool_name == "test"
        assert ctx.action == ""
        assert ctx.user_id == ""
        assert ctx.user_role == ""
        assert ctx.parameters == {}
        assert ctx.metadata == {}
        assert ctx.session_id == ""
        assert ctx.trace_id == ""

    def test_full_context(self):
        ctx = ToolContext(
            tool_name="appointment",
            action="book",
            user_id="user_1",
            user_role="patient",
            patient_id="pat_1",
            doctor_id="doc_1",
            parameters={"scheduled_at": "2026-07-16T10:00:00Z"},
            metadata={"source": "chat"},
            session_id="session_1",
            trace_id="trace_1",
        )
        assert ctx.tool_name == "appointment"
        assert ctx.action == "book"
        assert ctx.patient_id == "pat_1"
        assert ctx.doctor_id == "doc_1"

    def test_parameters_mutable(self):
        ctx = ToolContext(tool_name="test")
        ctx.parameters["key"] = "value"
        assert ctx.parameters["key"] == "value"

    def test_metadata_mutable(self):
        ctx = ToolContext(tool_name="test")
        ctx.metadata["key"] = "value"
        assert ctx.metadata["key"] == "value"
