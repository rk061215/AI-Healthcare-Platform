from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.pagination import PaginatedResponse


class DocumentMetadata(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    pages: Optional[int] = None
    author: Optional[str] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    camera_model: Optional[str] = None
    capture_date: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None


class DocumentResponse(BaseModel):
    id: str
    patient_id: str
    uploaded_by: Optional[str] = None
    uploaded_by_role: str
    original_filename: str
    file_type: str
    file_size: int
    mime_type: Optional[str] = None
    storage_provider: str
    content_hash: str
    doc_metadata: Optional[dict] = None
    virus_scan_status: str
    virus_scan_result: Optional[str] = None
    document_group_id: str
    version: int
    is_latest_version: bool
    status: str
    error_message: Optional[str] = None
    uploaded_at: datetime
    created_at: datetime
    updated_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "patient_id", "uploaded_by", "document_group_id", mode="before")
    @classmethod
    def convert_uuid_to_str(cls, v: object) -> str:
        return str(v) if v is not None else v


class DocumentUploadResponse(BaseModel):
    id: str
    document_group_id: str
    version: int
    original_filename: str
    file_type: str
    file_size: int
    status: str
    virus_scan_status: str
    uploaded_at: datetime


class DocumentVersionResponse(BaseModel):
    id: str
    version: int
    original_filename: str
    file_type: str
    file_size: int
    is_latest_version: bool
    status: str
    uploaded_at: datetime
    uploaded_by_role: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def convert_id_to_str(cls, v: object) -> str:
        return str(v) if v is not None else v


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class DocumentStatusUpdate(BaseModel):
    status: str
    virus_scan_status: Optional[str] = None
    virus_scan_result: Optional[str] = None
    error_message: Optional[str] = None
