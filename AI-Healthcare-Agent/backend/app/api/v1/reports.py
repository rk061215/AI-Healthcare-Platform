import time
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from app.api.deps import get_current_patient, get_db
from app.core.config import settings
from app.core.exceptions import ValidationException
from app.services.ocr_service import OcrService
from app.services.report_service import ReportService

router = APIRouter()


ALLOWED_TYPES = {".pdf", ".jpg", ".jpeg", ".png"}


@router.post("/upload")
async def upload_report(
    file: UploadFile = File(...),
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    patient_id = payload.get("sub")
    logger.info(f"[PIPELINE AUDIT] === UPLOAD ENTERED === patient_id={patient_id}")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_TYPES:
        raise ValidationException(f"File type {ext} not allowed")

    content = await file.read()
    logger.info(f"[PIPELINE AUDIT] Upload — filename={file.filename}, size={len(content)} bytes, ext={ext}")

    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise ValidationException(f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    file_id = str(uuid.uuid4())
    file_path = settings.upload_path / f"{file_id}{ext}"
    file_path.write_bytes(content)

    service = ReportService(db)
    report = service.create_report(
        patient_id=patient_id,
        file_path=str(file_path),
        file_type=ext.lstrip("."),
        title=file.filename,
    )
    logger.info(f"[PIPELINE AUDIT] Upload — report created: id={report.id}, status={report.status}, file_type={report.file_type}")

    logger.info(f"[PIPELINE AUDIT] Upload — returning status={report.status}. NOTE: OCR processing is NOT auto-scheduled. Frontend must call POST /{{id}}/process separately.")

    return {
        "id": str(report.id),
        "title": report.title,
        "status": report.status,
        "uploaded_at": report.uploaded_at.isoformat(),
    }


@router.post("/{report_id}/process")
def process_report_ocr(
    report_id: str,
    background_tasks: BackgroundTasks,
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    from app.database.enums import ReportStatus
    from app.models.report import Report as ReportModel
    from app.services.ocr_service import run_background_ocr

    patient_id = payload.get("sub")
    logger.info(f"[PIPELINE AUDIT] === PROCESS ENTERED === report_id={report_id}, patient_id={patient_id}")

    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        raise ValidationException(f"Invalid report ID format: {report_id}")

    report = db.query(ReportModel).filter(ReportModel.id == report_uuid).first()
    if not report:
        logger.warning(f"[PIPELINE AUDIT] Process — report NOT FOUND: {report_id}")
        raise ValidationException(f"Report {report_id} not found")

    logger.info(f"[PIPELINE AUDIT] Process — report found: id={report_id}, current_status={report.status}, file_type={report.file_type}")

    report.status = ReportStatus.PROCESSING
    db.commit()

    background_tasks.add_task(run_background_ocr, report_id)
    logger.info(f"[PIPELINE AUDIT] Process — background_task scheduled for report_id={report_id}")

    logger.info(f"[PIPELINE AUDIT] Process — returning HTTP 200 with status=processing, report_id={report_id}")

    return {
        "id": report_id,
        "status": "processing",
        "message": "Report processing started in background",
    }


@router.post("/{report_id}/retry")
def retry_report_ocr(
    report_id: str,
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = OcrService(db)
    result = service.retry_failed_report(report_id)
    return result


@router.post("/process-pending")
def process_pending_reports(
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = OcrService(db)
    results = service.process_pending_reports()
    return {"processed": len(results), "results": results}


@router.get("")
def list_reports(
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    reports = service.get_patient_reports(payload["sub"])
    return [
        {
            "id": str(r.id),
            "title": r.title,
            "file_type": r.file_type,
            "status": r.status,
            "ocr_confidence": r.ocr_confidence,
            "ocr_provider": r.ocr_provider,
            "ocr_pages": r.ocr_pages,
            "retry_count": r.retry_count,
            "uploaded_at": r.uploaded_at.isoformat(),
            "processed_at": r.processed_at.isoformat() if r.processed_at else None,
        }
        for r in reports
    ]


@router.get("/{report_id}")
def get_report(
    report_id: str,
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    report = service.get_report(report_id)
    return {
        "id": str(report.id),
        "title": report.title,
        "file_type": report.file_type,
        "status": report.status,
        "ocr_text": report.ocr_text,
        "ocr_confidence": report.ocr_confidence,
        "ocr_provider": report.ocr_provider,
        "ocr_pages": report.ocr_pages,
        "retry_count": report.retry_count,
        "preprocessing_applied": report.preprocessing_applied,
        "extracted_data": report.extracted_data,
        "error_message": report.error_message,
        "uploaded_at": report.uploaded_at.isoformat(),
        "processed_at": report.processed_at.isoformat() if report.processed_at else None,
    }


@router.delete("/{report_id}")
def delete_report(
    report_id: str,
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = ReportService(db)
    service.delete_report(report_id)
    return {"message": "Report deleted successfully"}
