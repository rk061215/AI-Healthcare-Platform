from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.tools.base_tool import BaseTool
from app.tools.exceptions import ToolValidationError
from app.tools.tool_context import ToolContext
from app.tools.tool_result import ToolResult


class DoctorTool(BaseTool):
    def validate(self, context: ToolContext) -> None:
        super().validate(context)
        if not context.action:
            raise ToolValidationError("action is required for doctor tool")
        valid_actions = {"assigned_doctor", "specialization", "availability"}
        if context.action not in valid_actions:
            raise ToolValidationError(
                f"Invalid action '{context.action}'. Valid: {valid_actions}"
            )

    def authorize(self, context: ToolContext) -> bool:
        return bool(context.user_id)

    def execute(self, context: ToolContext) -> ToolResult:
        db_session: Optional[Session] = context.parameters.get("db_session")
        if db_session is None:
            return ToolResult.error_factory(
                error_message="db_session is required in parameters",
                tool_name=context.tool_name,
                action=context.action,
            )

        action_map = {
            "assigned_doctor": self._assigned_doctor,
            "specialization": self._specialization,
            "availability": self._availability,
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

    def _assigned_doctor(self, db_session: Session, context: ToolContext) -> ToolResult:
        from app.services.patient_service import PatientService
        patient_id = context.parameters.get("patient_id", context.patient_id)
        if not patient_id:
            return ToolResult.error_factory(
                error_message="patient_id is required",
                tool_name=context.tool_name,
                action=context.action,
            )
        service = PatientService(db_session)
        doctors = service.get_patient_doctors(patient_id)
        doctor_list = [
            {
                "id": str(d.id),
                "full_name": d.full_name,
                "specialization": d.specialization,
                "phone": d.phone,
                "hospital_name": d.hospital_name,
            }
            for d in doctors
        ]
        return ToolResult.ok(
            data={"patient_id": patient_id, "doctors": doctor_list},
            tool_name=context.tool_name,
            action=context.action,
        )

    def _specialization(self, db_session: Session, context: ToolContext) -> ToolResult:
        from app.services.doctor_service import DoctorService
        doctor_id = context.parameters.get("doctor_id", context.doctor_id)
        if not doctor_id:
            return ToolResult.error_factory(
                error_message="doctor_id is required",
                tool_name=context.tool_name,
                action=context.action,
            )
        service = DoctorService(db_session)
        doctor = service.get_doctor(doctor_id)
        return ToolResult.ok(
            data={
                "doctor_id": str(doctor.id),
                "full_name": doctor.full_name,
                "specialization": doctor.specialization,
                "hospital_name": doctor.hospital_name,
                "years_of_experience": doctor.years_of_experience,
            },
            tool_name=context.tool_name,
            action=context.action,
        )

    def _availability(self, db_session: Session, context: ToolContext) -> ToolResult:
        from app.services.appointment_service import AppointmentService
        doctor_id = context.parameters.get("doctor_id", context.doctor_id)
        date_str = context.parameters.get("date", "")
        if not doctor_id:
            return ToolResult.error_factory(
                error_message="doctor_id is required",
                tool_name=context.tool_name,
                action=context.action,
            )
        service = AppointmentService(db_session)
        if date_str:
            slots = service.get_available_slots(doctor_id, date_str)
        else:
            slots = service.get_availability(doctor_id)
        return ToolResult.ok(
            data={"doctor_id": doctor_id, "slots": slots},
            tool_name=context.tool_name,
            action=context.action,
        )
