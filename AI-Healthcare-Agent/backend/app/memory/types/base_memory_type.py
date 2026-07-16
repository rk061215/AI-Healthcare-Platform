from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from app.memory.models import MEMORY_SCHEMA_VERSION, MemoryEntry, MemoryType


class BaseMemoryType:
    def __init__(self, memory_type: MemoryType) -> None:
        self._memory_type = memory_type

    @property
    def memory_type(self) -> MemoryType:
        return self._memory_type

    def _build_entry(
        self,
        session_id: str,
        content: dict[str, Any],
        importance: float = 0.5,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MemoryEntry:
        now = datetime.utcnow()
        expires_at = None
        if ttl_seconds is not None:
            expires_at = now + timedelta(seconds=ttl_seconds)
        return MemoryEntry(
            memory_id=str(uuid.uuid4()),
            session_id=session_id,
            memory_type=self._memory_type,
            content=content,
            importance=importance,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
            metadata=metadata or {},
        )
