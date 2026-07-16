from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from app.tools.base_tool import BaseTool
from app.tools.exceptions import (
    ToolAuthorizationError,
    ToolExecutionError,
    ToolServiceError,
    ToolValidationError,
)
from app.tools.tool_context import ToolContext
from app.tools.tool_result import ToolResult


class AppointmentTool(BaseTool):
    def validate(self, context: ToolContext) -> None:
        super().validate(context)
        if not context.action:
            raise ToolValidationError("action is required for appointment tool")
        valid_actions = {"book", "cancel", "reschedule", "list"}
        if context.action not in valid_actions:
            raise ToolValidationError(
                f"Invalid action '{context.action}'. Valid: {valid_actions}"
            )

    def authorize(self, context: ToolContext) -> bool:
        if context.action in ("book", "cancel", "reschedule"):
            if not context.user_id:
                return False
            if context.user_role not in ("patient", "doctor"):
                return False
        return True

    def execute(self, context: ToolContext) -> ToolResult:
        db_session: Optional[Session] = context.parameters.get("db_session")
        if db_session is None:
            return ToolResult.error_factory(
                error_message="db_session is required in parameters",
                tool_name=context.tool_name,
                action=context.action,
            )

        from app.services.appointment_service import AppointmentService
        service = AppointmentService(db_session)

        action_map = {
            "book": self._book,
            "cancel": self._cancel,
            "reschedule": self._reschedule,
            "list": self._list,
        }
        handler = action_map.get(context.action)
        if handler is None:
            return ToolResult.error_factory(
                error_message=f"Unknown action: {context.action}",
                tool_name=context.tool_name,
                action=context.action,
            )

        try:
            return handler(service, context)
        except Exception as exc:
            return ToolResult.error_factory(
                error_message=str(exc),
                tool_name=context.tool_name,
                action=context.action,
                metadata={"error_type": type(exc).__name__},
            )

    def _book(self, service: Any, context: ToolContext) -> ToolResult:
        data = {
            "patient_id": context.parameters.get("patient_id", context.patient_id),
            "doctor_id": context.parameters.get("doctor_id", context.doctor_id),
            "scheduled_at": context.parameters.get("scheduled_at"),
            "title": context.parameters.get("title", "Medical Appointment"),
            "description": context.parameters.get("description"),
            "duration_minutes": context.parameters.get("duration_minutes", 30),
        }
        if not data["doctor_id"] or not data["scheduled_at"]:
            return ToolResult.error_factory(
                error_message="doctor_id and scheduled_at are required",
                tool_name=context.tool_name,
                action=context.action,
            )
        appointment = service.create_appointment(data, context.user_id, context.user_role)
        return ToolResult.ok(
            data={"appointment_id": str(appointment.id), "status": appointment.status.value},
            tool_name=context.tool_name,
            action=context.action,
        )

    def _cancel(self, service: Any, context: ToolContext) -> ToolResult:
        appointment_id = context.parameters.get("appointment_id")
        reason = context.parameters.get("reason", "Cancelled by user")
        if not appointment_id:
            return ToolResult.error_factory(
                error_message="appointment_id is required",
                tool_name=context.tool_name,
                action=context.action,
            )
        appointment = service.cancel_appointment(
            appointment_id, reason, context.user_id, context.user_role,
        )
        return ToolResult.ok(
            data={"appointment_id": str(appointment.id), "status": appointment.status.value},
            tool_name=context.tool_name,
            action=context.action,
        )

    def _reschedule(self, service: Any, context: ToolContext) -> ToolResult:
        appointment_id = context.parameters.get("appointment_id")
        scheduled_at = context.parameters.get("scheduled_at")
        reason = context.parameters.get("reason")
        if not appointment_id or not scheduled_at:
            return ToolResult.error_factory(
                error_message="appointment_id and scheduled_at are required",
                tool_name=context.tool_name,
                action=context.action,
            )
        appointment = service.reschedule_appointment(
            appointment_id, scheduled_at, reason, context.user_id, context.user_role,
        )
        return ToolResult.ok(
            data={"appointment_id": str(appointment.id), "status": appointment.status.value},
            tool_name=context.tool_name,
            action=context.action,
        )

    def _list(self, service: Any, context: ToolContext) -> ToolResult:
        result = service.list_appointments(
            user_id=context.user_id,
            role=context.user_role,
            status=context.parameters.get("status"),
            page=context.parameters.get("page", 1),
            per_page=context.parameters.get("per_page", 20),
        )
        appointments = []
        if hasattr(result, "items"):
            for item in result.items:
                appointments.append({
                    "id": str(item.get("id", "")),
                    "title": item.get("title", ""),
                    "scheduled_at": str(item.get("scheduled_at", "")),
                    "status": item.get("status", ""),
                    "doctor_name": item.get("doctor_name", ""),
                })
        elif isinstance(result, dict) and "items" in result:
            appointments = result["items"]
        return ToolResult.ok(
            data={"appointments": appointments, "total": len(appointments)},
            tool_name=context.tool_name,
            action=context.action,
        )
