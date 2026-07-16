from app.tools.base_tool import BaseTool
from app.tools.config import ToolConfig
from app.tools.exceptions import (
    ToolAuthorizationError,
    ToolConfigError,
    ToolContextError,
    ToolError,
    ToolExecutionError,
    ToolNotFoundError,
    ToolRegistrationError,
    ToolRetryExhaustedError,
    ToolSelectorError,
    ToolServiceError,
    ToolTimeoutError,
    ToolValidationError,
    ToolVerificationError,
)
from app.tools.tool_context import ToolContext
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_factory import ToolFactory
from app.tools.tool_registry import ToolRegistry, get_global_registry
from app.tools.tool_result import ToolResult
from app.tools.tool_selector import ToolSelector
from app.tools.tool_service import ToolService
from app.tools.tools import (
    AppointmentTool,
    CalendarTool,
    DoctorTool,
    EmailTool,
    MedicationTool,
    NotificationTool,
    PatientTool,
    ReportTool,
    SMSTool,
)

_global_registry = get_global_registry()
_global_registry.register("appointment", AppointmentTool)
_global_registry.register("patient", PatientTool)
_global_registry.register("doctor", DoctorTool)
_global_registry.register("report", ReportTool)
_global_registry.register("medication", MedicationTool)
_global_registry.register("notification", NotificationTool)
_global_registry.register("calendar", CalendarTool)
_global_registry.register("email", EmailTool)
_global_registry.register("sms", SMSTool)

__all__ = [
    "BaseTool",
    "ToolConfig",
    "ToolContext",
    "ToolResult",
    "ToolRegistry",
    "ToolFactory",
    "ToolExecutor",
    "ToolSelector",
    "ToolService",
    "get_global_registry",
    "ToolError",
    "ToolNotFoundError",
    "ToolRegistrationError",
    "ToolValidationError",
    "ToolAuthorizationError",
    "ToolExecutionError",
    "ToolVerificationError",
    "ToolTimeoutError",
    "ToolRetryExhaustedError",
    "ToolContextError",
    "ToolConfigError",
    "ToolServiceError",
    "ToolSelectorError",
    "AppointmentTool",
    "PatientTool",
    "DoctorTool",
    "ReportTool",
    "MedicationTool",
    "NotificationTool",
    "CalendarTool",
    "EmailTool",
    "SMSTool",
]
