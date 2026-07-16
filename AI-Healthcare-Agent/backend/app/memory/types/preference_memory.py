from __future__ import annotations

from typing import Any, Optional

from app.memory.models import (
    MEMORY_SCHEMA_VERSION,
    MemoryEntry,
    MemoryType,
    PreferenceMemoryData,
)
from app.memory.types.base_memory_type import BaseMemoryType


class PreferenceMemory(BaseMemoryType):
    def __init__(self) -> None:
        super().__init__(memory_type=MemoryType.PREFERENCE)

    def create_entry(
        self,
        session_id: str,
        preference_type: str,
        preference_key: str,
        preference_value: Any,
        category: str = "general",
        importance: float = 0.6,
    ) -> MemoryEntry:
        data = PreferenceMemoryData(
            preference_type=preference_type,
            preference_key=preference_key,
            preference_value=preference_value,
            category=category,
        )
        return self._build_entry(
            session_id=session_id,
            content=data.model_dump(),
            importance=importance,
            metadata={"preference_type": preference_type, "category": category},
        )

    def get_preferences(
        self,
        entries: list[MemoryEntry],
        category: Optional[str] = None,
    ) -> list[PreferenceMemoryData]:
        result: list[PreferenceMemoryData] = []
        for entry in entries:
            if entry.memory_type == MemoryType.PREFERENCE:
                try:
                    data = PreferenceMemoryData(**entry.content)
                    if category is None or data.category == category:
                        result.append(data)
                except Exception:
                    continue
        return result
