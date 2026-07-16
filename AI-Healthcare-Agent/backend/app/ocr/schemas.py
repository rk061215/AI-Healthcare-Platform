from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OcrPageResult(BaseModel):
    page_number: int
    text: str
    confidence: float
    language: str = "en"
    processing_time_ms: float = 0.0
    preprocessed: bool = False


class OcrWord(BaseModel):
    text: str
    confidence: float
    bounding_box: Optional[list[int]] = None


class OcrBlock(BaseModel):
    text: str
    confidence: float
    block_type: str = "text"
    words: list[OcrWord] = []


class OcrResult(BaseModel):
    full_text: str
    confidence: float
    provider: str
    pages: list[OcrPageResult] = []
    blocks: list[OcrBlock] = []
    language: str = "en"
    processing_time_ms: float = 0.0
    has_more_pages: bool = False


class ExtractedField(BaseModel):
    name: str
    value: str
    confidence: float
    source_text: str = ""


class StructuredDocument(BaseModel):
    patient_name: Optional[str] = None
    patient_dob: Optional[str] = None
    document_date: Optional[str] = None
    doctor_name: Optional[str] = None
    diagnosis: Optional[str] = None
    medications: list[dict] = []
    lab_results: list[dict] = []
    notes: Optional[str] = None
    raw_fields: list[ExtractedField] = []


class OcrJobResult(BaseModel):
    report_id: str
    status: str
    provider: str
    confidence: float
    pages_processed: int
    text_length: int
    full_text: str = ""
    extracted_data: Optional[dict] = None
    preprocessing_applied: Optional[dict] = None
    processing_time_ms: float
    retry_count: int
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None
