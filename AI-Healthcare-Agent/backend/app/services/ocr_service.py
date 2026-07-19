import hashlib
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundException, ValidationException
from app.database.enums import IndexStatus, ReportStatus
from app.document_pipeline.pipeline import DocumentPipeline
from app.models.report import Report
from app.models.vector_index_state import VectorIndexState
from app.ocr.engine import OcrEngine
from app.ocr.schemas import OcrJobResult
from app.repositories.report_repository import ReportRepository
from app.vector_store.vector_service import VectorService


def run_background_ocr(report_id: str) -> None:
    from app.database.session import SessionLocal

    logger.info(f"[BG OCR] Starting background processing for report {report_id}")
    t0 = time.time()
    db = SessionLocal()
    try:
        service = OcrService(db)
        result = service.process_report(report_id)
        elapsed = time.time() - t0
        logger.info(
            f"[BG OCR] Report {report_id} finished: status={result.status}, "
            f"confidence={result.confidence}, pages={result.pages_processed}, "
            f"duration={elapsed:.1f}s"
        )
    except Exception as exc:
        elapsed = time.time() - t0
        logger.error(f"[BG OCR] Report {report_id} failed after {elapsed:.1f}s: {exc}")
        try:
            import uuid
            report = db.query(Report).filter(Report.id == uuid.UUID(report_id)).first()
            if report and str(report.status) == "processing":
                report.status = ReportStatus.FAILED
                report.error_message = str(exc)[:500]
                report.processed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


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

            saved_result = self._save_ocr_result(report, result)

            if result.status == "completed" and report.ocr_text:
                try:
                    self._index_report(report)
                except Exception as exc:
                    logger.warning(f"Report {report_id} OCR succeeded but indexing failed: {exc}")

            return saved_result

        except Exception as e:
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
            report.processed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(report)
            raise

    def _index_report(self, report: Report) -> None:
        pipeline = DocumentPipeline()
        vector_service = VectorService()

        chunks = pipeline.process(
            raw_text=report.ocr_text,
            patient_id=str(report.patient_id),
            report_id=str(report.id),
            source="ocr",
            language="en",
            provider=report.ocr_provider or "unknown",
        )

        if not chunks:
            logger.warning(f"Report {report.id} produced zero chunks — skipping vector index")
            return

        vector_service.index_chunks(chunks)

        chunk_text = " ".join(c.text for c in chunks)
        checksum = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()

        existing = (
            self.db.query(VectorIndexState)
            .filter(VectorIndexState.report_id == report.id)
            .first()
        )

        if existing:
            existing.chunk_count = len(chunks)
            existing.index_status = IndexStatus.INDEXED.value
            existing.index_checksum = checksum
            existing.last_indexed_at = datetime.now(timezone.utc)
        else:
            entry = VectorIndexState(
                report_id=report.id,
                patient_id=report.patient_id,
                chunk_count=len(chunks),
                index_status=IndexStatus.INDEXED.value,
                index_checksum=checksum,
                last_indexed_at=datetime.now(timezone.utc),
            )
            self.db.add(entry)

        self.db.commit()
        logger.info(f"Report {report.id}: {len(chunks)} chunks indexed to vector store")

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
