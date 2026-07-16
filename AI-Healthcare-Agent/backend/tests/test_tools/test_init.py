from __future__ import annotations

import app.tools
from app.tools import (
    AppointmentTool,
    BaseTool,
    CalendarTool,
    DoctorTool,
    EmailTool,
    MedicationTool,
    NotificationTool,
    PatientTool,
    ReportTool,
    SMSTool,
    ToolAuthorizationError,
    ToolConfig,
    ToolConfigError,
    ToolContext,
    ToolContextError,
    ToolError,
    ToolExecutionError,
    ToolFactory,
    ToolNotFoundError,
    ToolRegistrationError,
    ToolResult,
    ToolRetryExhaustedError,
    ToolSelector,
    ToolSelectorError,
    ToolService,
    ToolServiceError,
    ToolTimeoutError,
    ToolValidationError,
    ToolVerificationError,
)
from app.tools.tool_registry import get_global_registry


class TestInit:
    def test_core_classes_exported(self):
        assert BaseTool is not None
        assert ToolConfig is not None
        assert ToolContext is not None
        assert ToolResult is not None
        assert ToolFactory is not None
        assert ToolSelector is not None
        assert ToolService is not None

    def test_exceptions_exported(self):
        assert ToolError is not None
        assert ToolNotFoundError is not None
        assert ToolRegistrationError is not None
        assert ToolValidationError is not None
        assert ToolAuthorizationError is not None
        assert ToolExecutionError is not None
        assert ToolVerificationError is not None
        assert ToolTimeoutError is not None
        assert ToolRetryExhaustedError is not None
        assert ToolContextError is not None
        assert ToolConfigError is not None
        assert ToolServiceError is not None
        assert ToolSelectorError is not None

    def test_domain_tools_exported(self):
        assert AppointmentTool is not None
        assert PatientTool is not None
        assert DoctorTool is not None
        assert ReportTool is not None
        assert MedicationTool is not None

    def test_future_tools_exported(self):
        assert NotificationTool is not None
        assert CalendarTool is not None
        assert EmailTool is not None
        assert SMSTool is not None

    def test_global_registry_has_all_tools(self):
        registry = get_global_registry()
        tools = registry.list_tools()
        assert "appointment" in tools
        assert "patient" in tools
        assert "doctor" in tools
        assert "report" in tools
        assert "medication" in tools
        assert "notification" in tools
        assert "calendar" in tools
        assert "email" in tools
        assert "sms" in tools

    def test_all_exports_defined(self):
        assert hasattr(app.tools, "__all__")
        assert len(app.tools.__all__) > 20
