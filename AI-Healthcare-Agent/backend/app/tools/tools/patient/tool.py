from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.tools.base_tool import BaseTool
from app.tools.exceptions import ToolValidationError
from app.tools.tool_context import ToolContext
from app.tools.tool_result import ToolResult


class PatientTool(BaseTool):
    def validate(self, context: ToolContext) -> None:
        super().validate(context)
        if not context.action:
            raise ToolValidationError("action is required for patient tool")
        valid_actions = {"get_profile", "active_reports"}
        if context.action not in valid_actions:
            raise ToolValidationError(
                f"Invalid action '{context.action}'. Valid: {valid_actions}"
            )

    def authorize(self, context: ToolContext) -> bool:
        if not context.user_id:
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

        action_map = {
            "get_profile": self._get_profile,
            "active_reports": self._active_reports,
        }
        handler = action_map.get(context.action)
        if handler is None:
            return ToolResult.error_factory(
                error_message=f"Unknown action: {context.action}",
                tool_name=context.tool_name,
                action=context.action,
            )

        try:
            return handler(db_session, context)
        except Exception as exc:
            return ToolResult.error_factory(
                error_message=str(exc),
                tool_name=context.tool_name,
                action=context.action,
                metadata={"error_type": type(exc).__name__},
            )

    def _get_profile(self, db_session: Session, context: ToolContext) -> ToolResult:
        from app.services.patient_service import PatientService
        patient_id = context.parameters.get("patient_id", context.patient_id)
        if not patient_id:
            return ToolResult.error_factory(
                error_message="patient_id is required",
                tool_name=context.tool_name,
                action=context.action,
            )
        service = PatientService(db_session)
        patient = service.get_patient(patient_id)
        return ToolResult.ok(
            data={
                "patient_id": str(patient.id),
                "full_name": patient.full_name,
                "email": patient.email,
                "phone": patient.phone,
                "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
                "gender": patient.gender.value if patient.gender else None,
                "blood_group": patient.blood_group.value if patient.blood_group else None,
            },
            tool_name=context.tool_name,
            action=context.action,
        )

    def _active_reports(self, db_session: Session, context: ToolContext) -> ToolResult:
        from app.services.report_service import ReportService
        patient_id = context.parameters.get("patient_id", context.patient_id)
        if not patient_id:
            return ToolResult.error_factory(
                error_message="patient_id is required",
                tool_name=context.tool_name,
                action=context.action,
            )
        service = ReportService(db_session)
        reports = service.get_patient_reports(patient_id)
        report_list = [
            {
                "id": str(r.id),
                "title": r.title,
                "file_type": r.file_type,
                "status": r.status,
                "uploaded_at": str(r.uploaded_at),
            }
            for r in reports
        ]
        return ToolResult.ok(
            data={"patient_id": patient_id, "reports": report_list, "total": len(report_list)},
            tool_name=context.tool_name,
            action=context.action,
        )
