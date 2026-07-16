from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.tools.tool_context import ToolContext
from app.tools.tool_registry import get_global_registry
from app.tools.tool_service import ToolService
from app.tools.tool_selector import ToolSelector
from tests.test_tools.conftest import SimpleTool, FailingTool


class TestToolService:
    def test_run_with_tool_success(self):
        service = ToolService()
        tool = SimpleTool()
        ctx = ToolContext(tool_name="simple", action="act", user_id="u1")
        result = service.run_with_tool(tool, ctx)
        assert result.success is True
        assert result.data["message"] == "executed"

    def test_run_with_tool_failure(self):
        service = ToolService()
        tool = FailingTool()
        ctx = ToolContext(tool_name="failing", action="act", user_id="u1")
        result = service.run_with_tool(tool, ctx)
        assert result.success is False
        assert result.error == "execution failed"

    def test_run_unknown_tool(self):
        service = ToolService()
        result = service.run("nonexistent", action="act")
        assert result.success is False
        assert "ToolNotFoundError" in (result.metadata.get("error_type", "") or "")

    def test_list_tools(self):
        service = ToolService()
        tools = service.list_tools()
        assert "appointment" in tools
        assert "medication" in tools

    def test_run_from_query_success(self):
        service = ToolService()
        with patch("app.services.appointment_service.AppointmentService") as mock_svc:
            mock_instance = MagicMock()
            mock_svc.return_value = mock_instance
            mock_appointment = MagicMock()
            mock_appointment.id = "appt_1"
            mock_appointment.status.value = "scheduled"
            mock_instance.create_appointment.return_value = mock_appointment
            result = service.run_from_query("book appointment", user_id="u1",
                                            user_role="patient",
                                            parameters={"doctor_id": "doc_1",
                                                         "scheduled_at": "now",
                                                         "patient_id": "pat_1",
                                                         "db_session": MagicMock()})
        assert result.success is True

    def test_run_from_query_no_match(self):
        selector = ToolSelector()
        service = ToolService(selector=selector)
        result = service.run_from_query("what is the weather", user_id="u1")
        assert result.success is False
        assert "ToolSelectorError" in (result.metadata.get("error_type", "") or "")
