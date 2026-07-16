from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from app.memory.models import (
    DocumentContextData,
    MemoryEntry,
    MemoryType,
)
from app.memory.types.base_memory_type import BaseMemoryType


class DocumentContext(BaseMemoryType):
    def __init__(self) -> None:
        super().__init__(memory_type=MemoryType.DOCUMENT_CONTEXT)

    def create_entry(
        self,
        session_id: str,
        document_id: str,
        patient_id: str,
        report_id: str = "",
        document_type: str = "",
        version: str = "1.0.0",
        sections: Optional[list[str]] = None,
        importance: float = 0.8,
    ) -> MemoryEntry:
        data = DocumentContextData(
            document_id=document_id,
            patient_id=patient_id,
            report_id=report_id,
            document_type=document_type,
            version=version,
            upload_timestamp=datetime.utcnow(),
            sections=sections or [],
        )
        return self._build_entry(
            session_id=session_id,
            content=data.model_dump(),
            importance=importance,
            metadata={"document_id": document_id, "patient_id": patient_id},
        )

    def get_active_document(self, entries: list[MemoryEntry]) -> Optional[DocumentContextData]:
        for entry in sorted(entries, key=lambda e: e.created_at, reverse=True):
            if entry.memory_type == MemoryType.DOCUMENT_CONTEXT:
                try:
                    return DocumentContextData(**entry.content)
                except Exception:
                    continue
        return None
