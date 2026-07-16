from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_doctor, get_current_patient, get_current_user, get_db
from app.services.document_service import DocumentService

router = APIRouter()


def _get_service(db: Session) -> DocumentService:
    return DocumentService(db)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_group_id: str | None = Query(None),
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    content = await file.read()
    service = _get_service(db)
    result = service.upload(
        patient_id=payload["sub"],
        uploaded_by=payload["sub"],
        uploaded_by_role="patient",
        original_filename=file.filename or "unnamed",
        content=content,
        content_type=file.content_type or "application/octet-stream",
        document_group_id=document_group_id,
    )
    return result


@router.post("/doctor/upload")
async def doctor_upload_document(
    patient_id: str = Query(...),
    file: UploadFile = File(...),
    document_group_id: str | None = Query(None),
    payload: dict = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    content = await file.read()
    service = _get_service(db)
    result = service.upload(
        patient_id=patient_id,
        uploaded_by=payload["sub"],
        uploaded_by_role="doctor",
        original_filename=file.filename or "unnamed",
        content=content,
        content_type=file.content_type or "application/octet-stream",
        document_group_id=document_group_id,
    )
    return result


@router.get("")
def list_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    file_type: str | None = Query(None),
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = _get_service(db)
    return service.list_documents(
        patient_id=payload["sub"],
        page=page,
        per_page=per_page,
        file_type=file_type,
    )


@router.get("/{document_id}")
def get_document(
    document_id: str,
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = _get_service(db)
    return service.get_document(document_id, patient_id=payload["sub"])


@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = _get_service(db)
    content, filename, mime_type = service.download(document_id)
    return Response(
        content=content,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{document_id}/versions")
def get_document_versions(
    document_id: str,
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = _get_service(db)
    doc = service.get_document(document_id, patient_id=payload["sub"])
    return service.get_versions(doc.document_group_id)


@router.post("/{document_id}/retry")
async def retry_upload(
    document_id: str,
    file: UploadFile = File(...),
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    content = await file.read()
    service = _get_service(db)
    result = service.retry_upload(
        document_id=document_id,
        patient_id=payload["sub"],
        content=content,
        content_type=file.content_type or "application/octet-stream",
        original_filename=file.filename or "unnamed",
    )
    return result


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = _get_service(db)
    service.delete_document(document_id, patient_id=payload["sub"])
    return {"message": "Document deleted successfully"}
