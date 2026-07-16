from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChunkMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str = ""
    patient_id: Optional[str] = None
    report_id: Optional[str] = None
    document_type: str = "unknown"
    section: Optional[str] = None
    page: Optional[int] = None
    chunk_index: int = 0
    chunk_version: str = "1.0.0"
    schema_version: str = "1.0.0"
    embedding_version: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    provider: str = "unknown"
    language: str = "en"
    source: str = "ocr"
    chunker_type: str = "recursive"


class DocumentChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str = ""
    document_id: str = ""
    text: str
    metadata: ChunkMetadata = Field(default_factory=ChunkMetadata)
