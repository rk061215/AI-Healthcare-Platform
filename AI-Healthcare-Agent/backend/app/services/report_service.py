import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundException, ValidationException
from app.models.report import Report
from app.repositories.report_repository import ReportRepository


class ReportService:
    def __init__(self, db: Session):
        self.db = db
        self.report_repo = ReportRepository(db)

    def create_report(
        self,
        patient_id: str,
        file_path: str,
        file_type: str,
        title: str | None = None,
    ) -> Report:
        report = Report(
            patient_id=uuid.UUID(patient_id),
            file_path=file_path,
            file_type=file_type,
            title=title,
            status="pending",
            uploaded_at=datetime.now(timezone.utc),
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_report(self, report_id: str) -> Report:
        report = self.report_repo.get(uuid.UUID(report_id))
        if not report:
            raise NotFoundException("Report", report_id)
        return report

    def get_patient_reports(self, patient_id: str) -> list[Report]:
        return self.report_repo.get_by_patient(uuid.UUID(patient_id))

    def update_report_status(
        self,
        report_id: str,
        status: str,
        ocr_text: str | None = None,
        extracted_data: dict | None = None,
        error_message: str | None = None,
    ) -> Report:
        report = self.get_report(report_id)
        report.status = status
        if ocr_text is not None:
            report.ocr_text = ocr_text
        if extracted_data is not None:
            report.extracted_data = extracted_data
        if error_message is not None:
            report.error_message = error_message
        if status in ("completed", "failed"):
            report.processed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(report)
        return report

    def delete_report(self, report_id: str) -> None:
        report = self.get_report(report_id)
        file_path = Path(report.file_path)
        if file_path.exists():
            file_path.unlink()
        self.db.delete(report)
        self.db.commit()
