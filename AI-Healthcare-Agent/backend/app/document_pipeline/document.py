from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SectionInfo(BaseModel):
    header: str
    text: str
    page: Optional[int] = None
    index: int = 0


class ProcessedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw_text: str
    cleaned_text: str = ""
    document_type: str = "unknown"
    sections: list[SectionInfo] = []
    patient_id: Optional[str] = None
    report_id: Optional[str] = None
    source: str = "ocr"
    language: str = "en"
    provider: str = "unknown"
    page_count: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, str] = {}
