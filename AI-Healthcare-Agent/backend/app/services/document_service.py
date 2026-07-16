import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import NotFoundException, ValidationException
from app.database.enums import DocumentStatus, StorageProvider, VirusScanStatus
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import (
    DocumentMetadata,
    DocumentResponse,
    DocumentUploadResponse,
    DocumentVersionResponse,
)
from app.storage.backend import compute_content_hash, get_storage_backend


class DocumentService:
    ALLOWED_TYPES = {".pdf", ".png", ".jpg", ".jpeg"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
    }

    def __init__(self, db: Session):
        self.db = db
        self.repo = DocumentRepository(db)
        self.storage = get_storage_backend(StorageProvider.LOCAL)

    def upload(
        self,
        patient_id: str,
        uploaded_by: str,
        uploaded_by_role: str,
        original_filename: str,
        content: bytes,
        content_type: str,
        document_group_id: Optional[str] = None,
    ) -> DocumentUploadResponse:
        ext = self._validate_file(original_filename, content, content_type)

        if document_group_id:
            group_id = uuid.UUID(document_group_id)
            existing = self.repo.get_by_group(group_id)
            if not existing:
                raise NotFoundException("DocumentGroup", document_group_id)
        else:
            group_id = uuid.uuid4()

        content_hash = compute_content_hash(content)
        existing_doc = self.repo.get_by_content_hash(uuid.UUID(patient_id), content_hash)
        if existing_doc:
            raise ValidationException(
                "A document with identical content already exists for this patient"
            )

        file_id = str(uuid.uuid4())
        storage_path = self.storage.save(file_id, content, content_type)

        next_version = self.repo.get_next_version(group_id)

        extracted_metadata = self._extract_metadata(content, ext)

        doc = Document(
            patient_id=uuid.UUID(patient_id),
            uploaded_by=uuid.UUID(uploaded_by) if uploaded_by else None,
            uploaded_by_role=uploaded_by_role,
            original_filename=original_filename,
            file_type=ext.lstrip("."),
            file_size=len(content),
            mime_type=content_type,
            storage_path=storage_path,
            storage_provider=StorageProvider.LOCAL,
            content_hash=content_hash,
            doc_metadata=extracted_metadata.model_dump(exclude_none=True),
            virus_scan_status=VirusScanStatus.PENDING,
            document_group_id=group_id,
            version=next_version,
            is_latest_version=True,
            status=DocumentStatus.UPLOADED,
            uploaded_at=datetime.now(timezone.utc),
        )
        self.db.add(doc)
        self.db.flush()

        if next_version > 1:
            self.repo.mark_previous_versions_stale(group_id, doc.id)

        self.db.commit()
        self.db.refresh(doc)

        self._run_virus_scan(doc)

        return DocumentUploadResponse(
            id=str(doc.id),
            document_group_id=str(doc.document_group_id),
            version=doc.version,
            original_filename=doc.original_filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            status=doc.status.value if hasattr(doc.status, "value") else doc.status,
            virus_scan_status=doc.virus_scan_status.value if hasattr(doc.virus_scan_status, "value") else doc.virus_scan_status,
            uploaded_at=doc.uploaded_at,
        )

    def get_document(self, document_id: str, patient_id: Optional[str] = None) -> DocumentResponse:
        doc = self.repo.get(document_id)
        if not doc or not doc.is_active:
            raise NotFoundException("Document", document_id)
        if patient_id and str(doc.patient_id) != patient_id:
            raise NotFoundException("Document", document_id)
        return DocumentResponse.model_validate(doc)

    def list_documents(
        self,
        patient_id: str,
        page: int = 1,
        per_page: int = 20,
        file_type: Optional[str] = None,
    ) -> dict:
        skip = (page - 1) * per_page
        items, total = self.repo.get_by_patient(
            uuid.UUID(patient_id), file_type=file_type, skip=skip, limit=per_page
        )
        return {
            "items": [DocumentResponse.model_validate(d) for d in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }

    def get_versions(self, document_group_id: str) -> list[DocumentVersionResponse]:
        docs = self.repo.get_by_group(uuid.UUID(document_group_id))
        if not docs:
            raise NotFoundException("DocumentGroup", document_group_id)
        versions = []
        for d in docs:
            versions.append(
                DocumentVersionResponse(
                    id=str(d.id),
                    version=d.version,
                    original_filename=d.original_filename,
                    file_type=d.file_type,
                    file_size=d.file_size,
                    is_latest_version=d.is_latest_version,
                    status=d.status.value if hasattr(d.status, "value") else d.status,
                    uploaded_at=d.uploaded_at,
                    uploaded_by_role=d.uploaded_by_role,
                )
            )
        return versions

    def delete_document(self, document_id: str, patient_id: Optional[str] = None) -> None:
        doc = self.repo.get(document_id)
        if not doc or not doc.is_active:
            raise NotFoundException("Document", document_id)
        if patient_id and str(doc.patient_id) != patient_id:
            raise NotFoundException("Document", document_id)
        doc.soft_delete(deleted_by=patient_id)
        self.db.commit()

    def download(self, document_id: str, patient_id: Optional[str] = None) -> tuple[bytes, str, str]:
        doc = self.repo.get(document_id)
        if not doc or not doc.is_active:
            raise NotFoundException("Document", document_id)
        if patient_id and str(doc.patient_id) != patient_id:
            raise NotFoundException("Document", document_id)
        content = self.storage.get(doc.storage_path)
        if content is None:
            raise NotFoundException("DocumentFile", document_id)
        return content, doc.original_filename, doc.mime_type or "application/octet-stream"

    def retry_upload(
        self,
        document_id: str,
        patient_id: str,
        content: bytes,
        content_type: str,
        original_filename: str,
    ) -> DocumentUploadResponse:
        doc = self.repo.get(document_id)
        if not doc or not doc.is_active:
            raise NotFoundException("Document", document_id)
        if str(doc.patient_id) != patient_id:
            raise NotFoundException("Document", document_id)
        if doc.status != DocumentStatus.FAILED:
            raise ValidationException(
                "Only failed documents can be retried"
            )

        return self.upload(
            patient_id=patient_id,
            uploaded_by=patient_id,
            uploaded_by_role=doc.uploaded_by_role,
            original_filename=original_filename,
            content=content,
            content_type=content_type,
            document_group_id=str(doc.document_group_id),
        )

    def update_status(
        self,
        document_id: str,
        status: Optional[str] = None,
        virus_scan_status: Optional[str] = None,
        virus_scan_result: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> DocumentResponse:
        doc = self.repo.get(document_id)
        if not doc:
            raise NotFoundException("Document", document_id)
        if status:
            doc.status = status
        if virus_scan_status:
            doc.virus_scan_status = virus_scan_status
        if virus_scan_result is not None:
            doc.virus_scan_result = virus_scan_result
        if error_message is not None:
            doc.error_message = error_message
        self.db.commit()
        self.db.refresh(doc)
        return DocumentResponse.model_validate(doc)

    def _validate_file(
        self, original_filename: str, content: bytes, content_type: str
    ) -> str:
        ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
        ext = f".{ext}"

        if ext not in self.ALLOWED_TYPES:
            raise ValidationException(
                f"File type {ext} not allowed. Allowed types: {', '.join(self.ALLOWED_TYPES)}"
            )

        max_size = settings.DOCUMENT_MAX_SIZE_MB * 1024 * 1024
        if len(content) > max_size:
            raise ValidationException(
                f"File size {len(content) / 1024 / 1024:.1f}MB exceeds maximum of {settings.DOCUMENT_MAX_SIZE_MB}MB"
            )

        return ext

    def _extract_metadata(self, content: bytes, ext: str) -> DocumentMetadata:
        metadata = DocumentMetadata()
        if ext == ".pdf":
            metadata.pages = self._guess_pdf_page_count(content)
        elif ext in (".jpg", ".jpeg"):
            try:
                from io import BytesIO
                from PIL import Image
                img = Image.open(BytesIO(content))
                metadata.width, metadata.height = img.size
                exif_data = img._getexif() if hasattr(img, "_getexif") else None
                if exif_data:
                    for tag_id, value in exif_data.items():
                        from PIL.ExifTags import TAGS
                        tag_name = TAGS.get(tag_id, "")
                        if tag_name == "Model":
                            metadata.camera_model = str(value)
                        elif tag_name == "DateTimeOriginal":
                            metadata.capture_date = str(value)
                        elif tag_name == "GPSInfo":
                            try:
                                gps = {}
                                for k, v in value.items():
                                    from PIL.ExifTags import GPSTAGS
                                    gps_tag = GPSTAGS.get(k, k)
                                    gps[gps_tag] = v
                                if "GPSLatitude" in gps and "GPSLatitudeRef" in gps:
                                    lat = self._convert_gps_to_decimal(gps["GPSLatitude"])
                                    if gps["GPSLatitudeRef"] == "S":
                                        lat = -lat
                                    metadata.gps_latitude = lat
                                if "GPSLongitude" in gps and "GPSLongitudeRef" in gps:
                                    lon = self._convert_gps_to_decimal(gps["GPSLongitude"])
                                    if gps["GPSLongitudeRef"] == "W":
                                        lon = -lon
                                    metadata.gps_longitude = lon
                            except Exception:
                                pass
            except Exception:
                pass
        elif ext == ".png":
            try:
                from io import BytesIO
                from PIL import Image
                img = Image.open(BytesIO(content))
                metadata.width, metadata.height = img.size
            except Exception:
                pass
        return metadata

    def _guess_pdf_page_count(self, content: bytes) -> Optional[int]:
        try:
            import re
            text = content.decode("latin-1", errors="ignore")
            count = len(re.findall(rb"/Type\s*/Page[^s]", content))
            if count > 0:
                return count
            count2 = len(re.findall(r"/Type\s*/Page[^s]", text))
            return count2 if count2 > 0 else None
        except Exception:
            return None

    def _convert_gps_to_decimal(self, gps_data) -> float:
        degrees = float(gps_data[0])
        minutes = float(gps_data[1])
        seconds = float(gps_data[2])
        return degrees + minutes / 60.0 + seconds / 3600.0

    def _run_virus_scan(self, doc: Document) -> None:
        try:
            doc.virus_scan_status = VirusScanStatus.CLEAN
            doc.virus_scan_result = "No threats detected (placeholder)"
            self.db.commit()
        except Exception as e:
            doc.virus_scan_status = VirusScanStatus.ERROR
            doc.virus_scan_result = f"Scan error: {str(e)}"
            self.db.commit()
