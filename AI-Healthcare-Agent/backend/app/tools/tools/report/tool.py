from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.tools.base_tool import BaseTool
from app.tools.exceptions import ToolValidationError
from app.tools.tool_context import ToolContext
from app.tools.tool_result import ToolResult


class ReportTool(BaseTool):
    def validate(self, context: ToolContext) -> None:
        super().validate(context)
        if not context.action:
            raise ToolValidationError("action is required for report tool")
        valid_actions = {"list", "summarize", "metadata"}
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
            "list": self._list,
            "summarize": self._summarize,
            "metadata": self._metadata,
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

    def _list(self, db_session: Session, context: ToolContext) -> ToolResult:
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

    def _summarize(self, db_session: Session, context: ToolContext) -> ToolResult:
        report_id = context.parameters.get("report_id")
        if not report_id:
            return ToolResult.error_factory(
                error_message="report_id is required",
                tool_name=context.tool_name,
                action=context.action,
            )
        from app.services.report_service import ReportService
        service = ReportService(db_session)
        report = service.get_report(report_id)
        summary_parts = []
        if report.title:
            summary_parts.append(f"Title: {report.title}")
        summary_parts.append(f"Type: {report.file_type}")
        summary_parts.append(f"Status: {report.status}")
        summary_parts.append(f"Uploaded: {report.uploaded_at}")
        if report.ocr_text:
            summary_parts.append(f"Content preview: {report.ocr_text[:500]}")
        if report.extracted_data:
            summary_parts.append(f"Extracted data: {report.extracted_data}")
        return ToolResult.ok(
            data={
                "report_id": report_id,
                "summary": "\n".join(summary_parts),
                "status": report.status,
            },
            tool_name=context.tool_name,
            action=context.action,
        )

    def _metadata(self, db_session: Session, context: ToolContext) -> ToolResult:
        report_id = context.parameters.get("report_id")
        if not report_id:
            return ToolResult.error_factory(
                error_message="report_id is required",
                tool_name=context.tool_name,
                action=context.action,
            )
        from app.services.report_service import ReportService
        service = ReportService(db_session)
        report = service.get_report(report_id)
        return ToolResult.ok(
            data={
                "report_id": str(report.id),
                "title": report.title,
                "file_type": report.file_type,
                "file_size": report.file_size,
                "status": report.status,
                "uploaded_at": str(report.uploaded_at),
                "processed_at": str(report.processed_at) if report.processed_at else None,
                "ocr_confidence": report.ocr_confidence,
                "ocr_provider": report.ocr_provider,
                "patient_id": str(report.patient_id),
            },
            tool_name=context.tool_name,
            action=context.action,
        )
