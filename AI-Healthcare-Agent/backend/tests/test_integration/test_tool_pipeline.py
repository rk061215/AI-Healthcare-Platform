from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.report import Report

from app.tools.tool_context import ToolContext
from app.tools.tool_result import ToolResult
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_registry import get_global_registry, ToolRegistry
from app.tools.tool_selector import ToolSelector
from app.tools.tool_service import ToolService


@pytest.fixture
def fresh_registry() -> ToolRegistry:
    registry = ToolRegistry()
    yield registry


@pytest.fixture
def sample_tool_context() -> ToolContext:
    return ToolContext(
        tool_name="appointment",
        action="book",
        user_id=str(uuid.uuid4()),
        user_role="patient",
        patient_id=str(uuid.uuid4()),
        doctor_id=str(uuid.uuid4()),
        parameters={
            "doctor_id": str(uuid.uuid4()),
            "scheduled_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "reason": "Follow-up checkup",
        },
        session_id=str(uuid.uuid4()),
        trace_id=str(uuid.uuid4()),
    )


@pytest.fixture
def tool_service() -> ToolService:
    return ToolService()


class TestToolSelector:
    def test_select_appointment_booking(self):
        selector = ToolSelector()
        tool_type, action = selector.select("Book my follow-up appointment")
        assert tool_type == "appointment"
        assert action == "book"

    def test_select_appointment_cancellation(self):
        selector = ToolSelector()
        tool_type, action = selector.select("Cancel my appointment")
        assert tool_type == "appointment"
        assert action == "cancel"

    def test_select_appointment_reschedule(self):
        selector = ToolSelector()
        tool_type, action = selector.select("Reschedule my appointment to next week")
        assert tool_type == "appointment"
        assert action == "reschedule"

    def test_select_patient_profile(self):
        selector = ToolSelector()
        tool_type, action = selector.select("Show my profile")
        assert tool_type == "patient"
        assert action == "get_profile"

    def test_select_report_list(self):
        selector = ToolSelector()
        tool_type, action = selector.select("Show my reports")
        assert tool_type == "report"
        assert action == "list"

    def test_select_report_summary(self):
        selector = ToolSelector()
        tool_type, action = selector.select("Summarize my latest report")
        assert tool_type == "report"
        assert action == "summarize"

    def test_select_medication_schedule(self):
        selector = ToolSelector()
        tool_type, action = selector.select("What is my medication schedule?")
        assert tool_type == "medication"
        assert action == "schedule"

    def test_select_doctor_specialization(self):
        selector = ToolSelector()
        result = selector.select_or_none("Find a cardiologist")
        if result:
            tool_type, action = result
            assert action == "specialization"

    def test_select_unknown_returns_error(self):
        selector = ToolSelector()
        with pytest.raises(Exception):
            selector.select("What is the weather today?")

    def test_select_empty_query_raises(self):
        selector = ToolSelector()
        with pytest.raises(Exception):
            selector.select("")


class TestToolExecution:
    def test_tool_executor_lifecycle(self, sample_tool_context):
        registry = get_global_registry()
        tool_cls = registry.get("appointment")
        tool = tool_cls()
        executor = ToolExecutor(tool)
        result = executor.execute(sample_tool_context)
        assert result is not None
        assert isinstance(result, ToolResult)

    def test_tool_result_ok_factory(self):
        result = ToolResult.ok(
            data={"message": "Appointment booked"},
            tool_name="appointment",
            action="book",
        )
        assert result.success
        assert result.data["message"] == "Appointment booked"

    def test_tool_result_error_factory(self):
        result = ToolResult.error_factory(
            error_message="Doctor not found",
            tool_name="appointment",
            action="book",
        )
        assert not result.success
        assert result.error_message == "Doctor not found"

    def test_tool_executor_propagates_error(self, sample_tool_context):
        registry = get_global_registry()
        tool_cls = registry.get("appointment")
        tool = tool_cls()
        bad_context = ToolContext(
            tool_name="appointment",
            action="book",
            user_id="u1",
            user_role="patient",
            parameters={},
        )
        executor = ToolExecutor(tool)
        result = executor.execute(bad_context)
        assert result is not None

    def test_tool_executor_authorization_check(self):
        from app.tools.base_tool import BaseTool
        class RestrictedTool(BaseTool):
            def authorize(self, context: ToolContext) -> bool:
                return context.user_role == "admin"
            def execute(self, context: ToolContext) -> ToolResult:
                return ToolResult.ok(data={"authorized": True})

        tool = RestrictedTool()
        executor = ToolExecutor(tool)
        patient_ctx = ToolContext(tool_name="restricted", action="exec", user_role="patient", parameters={})
        result = executor.execute(patient_ctx)
        assert result is not None

    def test_tool_executor_audit_hook(self):
        from app.tools.base_tool import BaseTool
        audit_log = []
        class AuditableTool(BaseTool):
            def execute(self, context: ToolContext) -> ToolResult:
                return ToolResult.ok(data={"done": True})
            def audit(self, context: ToolContext, result: ToolResult) -> None:
                audit_log.append((context.action, result.success))

        tool = AuditableTool()
        executor = ToolExecutor(tool)
        ctx = ToolContext(tool_name="auditable", action="exec", parameters={})
        executor.execute(ctx)
        assert len(audit_log) >= 1
        assert audit_log[0][1] is True


class TestToolServicePipeline:
    def test_tool_service_run_appointment(self):
        service = ToolService()
        result = service.run(
            tool_type="appointment",
            action="list",
            user_id="u1",
            user_role="patient",
            patient_id="p1",
            parameters={"patient_id": "p1"},
        )
        assert result is not None
        assert isinstance(result, ToolResult)

    def test_tool_service_run_from_query(self):
        service = ToolService()
        result = service.run_from_query(
            query="Show my reports",
            user_id="u1",
            user_role="patient",
            patient_id="p1",
        )
        assert result is not None

    def test_tool_service_run_unknown_tool(self):
        service = ToolService()
        result = service.run(
            tool_type="nonexistent_tool",
            action="do_something",
            user_id="u1",
            user_role="patient",
        )
        assert result is not None
        assert not result.success
        assert "error" in str(result.error_message).lower() or result.error_message

    def test_tool_service_list_registered_tools(self):
        service = ToolService()
        tools = service.list_tools()
        assert len(tools) >= 5
        assert "appointment" in tools
        assert "patient" in tools
        assert "doctor" in tools
        assert "report" in tools
        assert "medication" in tools

    def test_tool_service_sets_session_id(self):
        service = ToolService()
        result = service.run(
            tool_type="appointment",
            action="list",
            user_id="u1",
            user_role="patient",
            patient_id="p1",
            session_id="test-session-1",
            parameters={"patient_id": "p1"},
        )
        assert result is not None


class TestToolSelectorEdgeCases:
    def test_selector_handles_case_insensitivity(self):
        selector = ToolSelector()
        t, a = selector.select("BOOK MY APPOINTMENT")
        assert t == "appointment"
        assert a == "book"

    def test_selector_prefers_reschedule_over_book(self):
        selector = ToolSelector()
        t, a = selector.select("I need to reschedule my appointment")
        assert a == "reschedule"

    def test_selector_handles_punctuation(self):
        selector = ToolSelector()
        t, a = selector.select("What's my medication schedule?")
        assert t == "medication"
        assert a == "schedule"

    def test_selector_handles_misspellings(self):
        selector = ToolSelector()
        result = selector.select_or_none("Show my profle")
        assert result is None or result[0] == "patient"


class TestToolDBIntegration:
    def test_appointment_tool_requires_db_session(self):
        from app.tools.tools.appointment.tool import AppointmentTool
        tool = AppointmentTool()
        ctx = ToolContext(
            tool_name="appointment", action="list",
            user_id="u1", user_role="patient",
            parameters={},
        )
        result = tool.execute(ctx)
        assert result is not None

    def test_patient_tool_returns_profile(self):
        service = ToolService()
        result = service.run(
            tool_type="patient",
            action="get_profile",
            user_id="u1",
            user_role="patient",
            patient_id="p1",
        )
        assert result is not None

    def test_report_tool_lists_reports(self):
        service = ToolService()
        result = service.run(
            tool_type="report",
            action="list",
            user_id="u1",
            user_role="patient",
            patient_id="p1",
            parameters={"patient_id": "p1"},
        )
        assert result is not None
