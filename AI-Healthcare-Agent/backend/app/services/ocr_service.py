import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundException, ValidationException
from app.database.enums import ReportStatus
from app.models.report import Report
from app.ocr.engine import OcrEngine
from app.ocr.schemas import OcrJobResult
from app.repositories.report_repository import ReportRepository


class OcrService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReportRepository(db)
        self.engine = OcrEngine(use_mock=settings.OCR_USE_MOCK)

    def process_report(self, report_id: str) -> OcrJobResult:
        report = self.repo.get(uuid.UUID(report_id))
        if not report:
            raise NotFoundException("Report", report_id)

        if not settings.OCR_ENABLED:
            raise ValidationException("OCR processing is disabled")

        report.status = ReportStatus.PROCESSING
        report.retry_count = (report.retry_count or 0) + 1
        self.db.commit()

        try:
            file_path = Path(report.file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Report file not found: {report.file_path}")

            file_type = report.file_type or "pdf"
            result = self.engine.process_document(
                file_path=file_path,
                file_type=file_type,
                retry_count=report.retry_count - 1,
            )

            return self._save_ocr_result(report, result)

        except Exception as e:
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
            report.processed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(report)
            raise

    def process_pending_reports(self, limit: int = 10) -> list[OcrJobResult]:
        pending = self.repo.get_pending_reports()
        results: list[OcrJobResult] = []
        for report in pending[:limit]:
            try:
                result = self.process_report(str(report.id))
                results.append(result)
            except Exception as e:
                report.status = ReportStatus.FAILED
                report.error_message = str(e)
                report.processed_at = datetime.now(timezone.utc)
                self.db.commit()
        return results

    def retry_failed_report(self, report_id: str) -> OcrJobResult:
        report = self.repo.get(uuid.UUID(report_id))
        if not report:
            raise NotFoundException("Report", report_id)
        if report.status != ReportStatus.FAILED:
            raise ValidationException(
                f"Cannot retry report in status '{report.status}'. Only failed reports can be retried."
            )

        report.status = ReportStatus.PENDING
        report.error_message = None
        self.db.commit()

        return self.process_report(report_id)

    def _save_ocr_result(self, report: Report, result: OcrJobResult) -> OcrJobResult:
        if result.status == "completed":
            report.status = ReportStatus.COMPLETED
        else:
            report.status = ReportStatus.FAILED

        report.ocr_provider = result.provider
        report.ocr_confidence = result.confidence
        report.ocr_pages = result.pages_processed
        report.retry_count = result.retry_count
        report.processed_at = datetime.now(timezone.utc)

        if result.full_text:
            report.ocr_text = result.full_text
        if result.extracted_data:
            report.extracted_data = result.extracted_data
        if result.preprocessing_applied:
            report.preprocessing_applied = result.preprocessing_applied
        if result.error_message:
            report.error_message = result.error_message

        self.db.commit()
        self.db.refresh(report)

        return result
