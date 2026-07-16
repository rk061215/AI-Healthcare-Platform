from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ReportBase(BaseModel):
    title: Optional[str] = None


class ReportCreate(ReportBase):
    patient_id: str
    file_path: str
    file_type: str


class ReportResponse(ReportBase):
    id: str
    patient_id: str
    doctor_id: Optional[str] = None
    file_path: str
    file_type: Optional[str] = None
    ocr_text: Optional[str] = None
    extracted_data: Optional[dict] = None
    status: str
    error_message: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReportStatusUpdate(BaseModel):
    status: str
    error_message: Optional[str] = None
    ocr_text: Optional[str] = None
    extracted_data: Optional[dict] = None
