from __future__ import annotations

from typing import Any, Optional

from app.memory.models import (
    MemoryEntry,
    MemoryType,
    PatientContextData,
)
from app.memory.types.base_memory_type import BaseMemoryType


class PatientContext(BaseMemoryType):
    def __init__(self) -> None:
        super().__init__(memory_type=MemoryType.PATIENT_CONTEXT)

    def create_entry(
        self,
        session_id: str,
        patient_id: str,
        language: str = "en",
        preferred_doctor_id: Optional[str] = None,
        notification_enabled: bool = True,
        notification_channels: Optional[list[str]] = None,
        timezone: str = "UTC",
        importance: float = 0.9,
    ) -> MemoryEntry:
        data = PatientContextData(
            patient_id=patient_id,
            language=language,
            preferred_doctor_id=preferred_doctor_id,
            notification_enabled=notification_enabled,
            notification_channels=notification_channels or ["email"],
            timezone=timezone,
        )
        return self._build_entry(
            session_id=session_id,
            content=data.model_dump(),
            importance=importance,
            metadata={"patient_id": patient_id},
        )

    def get_patient_context(self, entries: list[MemoryEntry]) -> Optional[PatientContextData]:
        for entry in entries:
            if entry.memory_type == MemoryType.PATIENT_CONTEXT:
                try:
                    return PatientContextData(**entry.content)
                except Exception:
                    continue
        return None
