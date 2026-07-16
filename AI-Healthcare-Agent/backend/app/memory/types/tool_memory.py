from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from app.memory.models import (
    MemoryEntry,
    MemoryType,
    ToolMemoryData,
)
from app.memory.types.base_memory_type import BaseMemoryType


class ToolMemory(BaseMemoryType):
    def __init__(self) -> None:
        super().__init__(memory_type=MemoryType.TOOL)

    def create_entry(
        self,
        session_id: str,
        tool_name: str,
        action: str,
        result: Optional[dict[str, Any]] = None,
        importance: float = 0.5,
    ) -> MemoryEntry:
        data = ToolMemoryData(
            tool_name=tool_name,
            action=action,
            result=result or {},
            timestamp=datetime.utcnow(),
        )
        return self._build_entry(
            session_id=session_id,
            content=data.model_dump(),
            importance=importance,
            metadata={"tool_name": tool_name, "action": action},
        )

    def get_last_action(
        self,
        entries: list[MemoryEntry],
        tool_name: str,
    ) -> Optional[ToolMemoryData]:
        for entry in sorted(entries, key=lambda e: e.created_at, reverse=True):
            if entry.memory_type == MemoryType.TOOL:
                try:
                    data = ToolMemoryData(**entry.content)
                    if data.tool_name == tool_name:
                        return data
                except Exception:
                    continue
        return None
