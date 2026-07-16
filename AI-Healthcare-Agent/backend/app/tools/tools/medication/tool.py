from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.tools.base_tool import BaseTool
from app.tools.exceptions import ToolValidationError
from app.tools.tool_context import ToolContext
from app.tools.tool_result import ToolResult


class MedicationTool(BaseTool):
    def validate(self, context: ToolContext) -> None:
        super().validate(context)
        if not context.action:
            raise ToolValidationError("action is required for medication tool")
        valid_actions = {"schedule", "explain"}
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
            "schedule": self._schedule,
            "explain": self._explain,
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

    def _schedule(self, db_session: Session, context: ToolContext) -> ToolResult:
        from app.services.medicine_service import MedicineService
        patient_id = context.parameters.get("patient_id", context.patient_id)
        if not patient_id:
            return ToolResult.error_factory(
                error_message="patient_id is required",
                tool_name=context.tool_name,
                action=context.action,
            )
        service = MedicineService(db_session)
        medicines = service.get_active_medicines(patient_id)
        med_list = [
            {
                "id": str(m.id),
                "name": m.name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "duration": m.duration,
                "route": m.route.value if m.route else None,
                "instructions": m.instructions,
                "start_date": str(m.start_date) if m.start_date else None,
                "end_date": str(m.end_date) if m.end_date else None,
            }
            for m in medicines
        ]
        return ToolResult.ok(
            data={
                "patient_id": patient_id,
                "medications": med_list,
                "total": len(med_list),
            },
            tool_name=context.tool_name,
            action=context.action,
        )

    def _explain(self, db_session: Session, context: ToolContext) -> ToolResult:
        medicine_name = context.parameters.get("medicine_name", "")
        medicine_id = context.parameters.get("medicine_id")
        if not medicine_name and not medicine_id:
            return ToolResult.error_factory(
                error_message="medicine_id or medicine_name is required",
                tool_name=context.tool_name,
                action=context.action,
            )
        from app.services.medicine_service import MedicineService
        service = MedicineService(db_session)
        if medicine_id:
            medicine = service.get_medicine(medicine_id)
        else:
            patient_id = context.parameters.get("patient_id", context.patient_id)
            if not patient_id:
                return ToolResult.error_factory(
                error_message="patient_id is required to look up medicine by name",
                    tool_name=context.tool_name,
                    action=context.action,
                )
            medicines = service.get_patient_medicines(patient_id)
            matches = [m for m in medicines if medicine_name.lower() in m.name.lower()]
            if not matches:
                return ToolResult.ok(
                    data={
                        "medicine_name": medicine_name,
                        "explanation": f"No medication found matching '{medicine_name}'",
                    },
                    tool_name=context.tool_name,
                    action=context.action,
                )
            medicine = matches[0]
        return ToolResult.ok(
            data={
                "medicine_id": str(medicine.id),
                "name": medicine.name,
                "dosage": medicine.dosage,
                "frequency": medicine.frequency,
                "duration": medicine.duration,
                "route": medicine.route.value if medicine.route else None,
                "instructions": medicine.instructions,
                "start_date": str(medicine.start_date) if medicine.start_date else None,
                "end_date": str(medicine.end_date) if medicine.end_date else None,
            },
            tool_name=context.tool_name,
            action=context.action,
        )
