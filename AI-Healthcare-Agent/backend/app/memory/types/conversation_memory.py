from __future__ import annotations

from typing import Any, Optional

from app.memory.models import (
    MEMORY_SCHEMA_VERSION,
    ConversationMemoryData,
    MemoryEntry,
    MemoryType,
)
from app.memory.types.base_memory_type import BaseMemoryType


class ConversationMemory(BaseMemoryType):
    def __init__(self) -> None:
        super().__init__(memory_type=MemoryType.CONVERSATION)

    def create_entry(
        self,
        session_id: str,
        turn_number: int,
        query: str,
        answer: str,
        query_type: str = "unknown",
        confidence: float = 0.0,
        follow_up: bool = False,
        importance: float = 0.5,
    ) -> MemoryEntry:
        data = ConversationMemoryData(
            turn_number=turn_number,
            query=query,
            answer=answer,
            query_type=query_type,
            confidence=confidence,
            follow_up=follow_up,
        )
        return self._build_entry(
            session_id=session_id,
            content=data.model_dump(),
            importance=importance,
            metadata={"turn_number": turn_number, "query_type": query_type},
        )

    def extract_turns(self, entries: list[MemoryEntry]) -> list[ConversationMemoryData]:
        result: list[ConversationMemoryData] = []
        for entry in entries:
            if entry.memory_type == MemoryType.CONVERSATION:
                try:
                    data = ConversationMemoryData(**entry.content)
                    result.append(data)
                except Exception:
                    continue
        return result

    def summarize_turns(self, entries: list[MemoryEntry]) -> str:
        turns = self.extract_turns(entries)
        if not turns:
            return ""
        parts: list[str] = []
        for t in turns:
            parts.append(f"User: {t.query}")
            parts.append(f"Assistant: {t.answer}")
        return "\n".join(parts)
