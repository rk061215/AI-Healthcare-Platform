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
from app.vector_recovery.config import get_embedding_model_key
from app.vector_store.vector_service import VectorService


def run_background_ocr(report_id: str) -> None:
    import traceback

    from app.database.session import SessionLocal

    logger.info(f"[BG OCR] Starting background processing for report {report_id}")
    logger.info(f"[PIPELINE AUDIT] === BACKGROUND TASK STARTED === report_id={report_id}")
    t0 = time.time()
    db = SessionLocal()
    logger.info(f"[PIPELINE AUDIT] Background OCR — DB session created for report_id={report_id}")
    try:
        service = OcrService(db)
        logger.info(f"[PIPELINE AUDIT] Background OCR — CALLING OcrService.process_report(report_id={report_id})")
        result = service.process_report(report_id)
        elapsed = time.time() - t0
        logger.info(f"[PIPELINE AUDIT] Background OCR — process_report RETURNED: status={result.status}, confidence={result.confidence}, provider={result.provider}, text_length={result.text_length}")
        logger.info(
            f"[BG OCR] Report {report_id} finished: status={result.status}, "
            f"confidence={result.confidence}, pages={result.pages_processed}, "
            f"duration={elapsed:.1f}s"
        )
    except Exception as exc:
        elapsed = time.time() - t0
        logger.error(f"[PIPELINE AUDIT] Background OCR — EXCEPTION: {traceback.format_exc()}")
        logger.error(f"[BG OCR] Report {report_id} failed after {elapsed:.1f}s: {exc}")
        try:
            import uuid
            report = db.query(Report).filter(Report.id == uuid.UUID(report_id)).first()
            if report and str(report.status) == "processing":
                report.status = ReportStatus.FAILED
                report.error_message = str(exc)[:500]
                report.processed_at = datetime.now(timezone.utc)
                db.commit()
                logger.info(f"[PIPELINE AUDIT] Background OCR — report {report_id} set to FAILED in exception handler")
        except Exception:
            pass
    finally:
        db.close()
        logger.info(f"[PIPELINE AUDIT] Background OCR — DB session closed for report_id={report_id}")


class OcrService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ReportRepository(db)
        self.engine = OcrEngine(use_mock=settings.OCR_USE_MOCK)

    def process_report(self, report_id: str) -> OcrJobResult:
        logger.info(f"[OCR AUDIT] process_report start — report_id={report_id}")
        logger.info(f"[PIPELINE AUDIT] === OCR SERVICE process_report ENTERED === report_id={report_id}")
        report = self.repo.get(uuid.UUID(report_id))
        if not report:
            logger.warning(f"[PIPELINE AUDIT] process_report — report NOT FOUND: {report_id}")
            raise NotFoundException("Report", report_id)

        if not settings.OCR_ENABLED:
            logger.warning(f"[PIPELINE AUDIT] process_report — OCR DISABLED by settings")
            raise ValidationException("OCR processing is disabled")

        logger.info(f"[PIPELINE AUDIT] process_report — report fetched: file_path={report.file_path}, file_type={report.file_type}, status={report.status}, retry_count={report.retry_count}")

        report.status = ReportStatus.PROCESSING
        report.retry_count = (report.retry_count or 0) + 1
        self.db.commit()

        try:
            file_path = Path(report.file_path)
            if not file_path.exists():
                logger.error(f"[PIPELINE AUDIT] process_report — file NOT FOUND on disk: {report.file_path}")
                raise FileNotFoundError(f"Report file not found: {report.file_path}")

            file_type = report.file_type or "pdf"
            logger.info(f"[PIPELINE AUDIT] process_report — Calling engine.process_document with file_path={file_path}, file_type={file_type}, retry_count={report.retry_count - 1}")
            result = self.engine.process_document(
                file_path=file_path,
                file_type=file_type,
                retry_count=report.retry_count - 1,
            )
            logger.info(f"[PIPELINE AUDIT] process_report — engine.process_document RETURNED: status={result.status}, confidence={result.confidence}, provider={result.provider}, text_length={result.text_length}, error_message={result.error_message!r}")

            saved_result = self._save_ocr_result(report, result)
            logger.info(f"[PIPELINE AUDIT] process_report — OCR result saved to DB: report_status={report.status}, confidence={report.ocr_confidence}")

            if result.status == "completed" and report.ocr_text:
                logger.info(f"[PIPELINE AUDIT] process_report — OCR completed, proceeding to indexing (text_length={len(report.ocr_text)})")
                try:
                    self._index_report(report)
                    report.status = ReportStatus.COMPLETED
                    self.db.commit()
                    logger.info(f"[PIPELINE AUDIT] process_report — Indexing succeeded, report COMPLETED")
                except Exception as exc:
                    logger.warning(f"[PIPELINE AUDIT] process_report — Indexing FAILED, setting report to FAILED: {exc}")
                    report.status = ReportStatus.FAILED
                    report.error_message = f"Indexing failed: {exc}"
                    self.db.commit()
            elif result.status == "completed":
                report.status = ReportStatus.COMPLETED
                self.db.commit()

            logger.info(f"[PIPELINE AUDIT] === OCR SERVICE process_report COMPLETE === report_id={report_id}, final_status={report.status}, ocr_confidence={report.ocr_confidence}")

            return saved_result

        except Exception as e:
            logger.error(f"[PIPELINE AUDIT] process_report — EXCEPTION: {type(e).__name__}: {e}")
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
            report.processed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(report)
            raise

    def _index_report(self, report: Report) -> None:
        logger.info(f"[PIPELINE AUDIT] === INDEXING STARTED === report_id={report.id}, ocr_text_length={len(report.ocr_text) if report.ocr_text else 0}")
        pipeline = DocumentPipeline()
        vector_service = VectorService()
        model_key = get_embedding_model_key(vector_service.embedding_service)
        logger.info(f"[PIPELINE AUDIT] _index_report — embedding_model_key={model_key}")

        logger.info(f"[PIPELINE AUDIT] _index_report — calling DocumentPipeline.process()")
        chunks = pipeline.process(
            raw_text=report.ocr_text,
            patient_id=str(report.patient_id),
            report_id=str(report.id),
            source="ocr",
            language="en",
            provider=report.ocr_provider or "unknown",
        )

        if not chunks:
            logger.warning(f"[PIPELINE AUDIT] _index_report — DocumentPipeline returned ZERO chunks — skipping vector index")
            return

        logger.info(f"[PIPELINE AUDIT] _index_report — DocumentPipeline returned {len(chunks)} chunks, calling VectorService.index_chunks()")

        index_t0 = time.time()
        vector_service.index_chunks(chunks)
        index_elapsed = (time.time() - index_t0) * 1000
        logger.info(f"[PIPELINE AUDIT] _index_report — VectorService.index_chunks() completed in {index_elapsed:.1f}ms, stored {len(chunks)} chunks")

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
            if not existing.embedding_model_version:
                existing.embedding_model_version = model_key
            logger.info(f"[PIPELINE AUDIT] _index_report — updated existing VectorIndexState: report_id={report.id}, chunk_count={len(chunks)}")
        else:
            entry = VectorIndexState(
                report_id=report.id,
                patient_id=report.patient_id,
                embedding_model_version=model_key,
                chunk_count=len(chunks),
                index_status=IndexStatus.INDEXED.value,
                index_checksum=checksum,
                last_indexed_at=datetime.now(timezone.utc),
            )
            self.db.add(entry)
            logger.info(f"[PIPELINE AUDIT] _index_report — created new VectorIndexState: report_id={report.id}, chunk_count={len(chunks)}")

        self.db.commit()
        logger.info(f"[PIPELINE AUDIT] === INDEXING COMPLETE === report_id={report.id}, {len(chunks)} chunks indexed, checksum={checksum[:12]}...")
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
        uploaded_at = report.uploaded_at.replace(tzinfo=timezone.utc) if report.uploaded_at else None
        processing_duration = (datetime.now(timezone.utc) - uploaded_at).total_seconds() if uploaded_at else 0

        if result.status == "completed":
            pass
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

        logger.info(f"[PIPELINE AUDIT] === OCR SAVED === report_id={report.id}, current_status={report.status}, ocr_confidence={report.ocr_confidence}, ocr_provider={report.ocr_provider}, ocr_pages={report.ocr_pages}, processing_duration={processing_duration:.1f}s, ocr_text_length={len(report.ocr_text) if report.ocr_text else 0}")

        return result
