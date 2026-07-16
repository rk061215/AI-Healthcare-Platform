from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from app.memory.exceptions import ExpiryPolicyViolationError
from app.memory.models import MemoryEntry, MemoryType


class ExpiryPolicy:
    def __init__(
        self,
        default_ttl_seconds: int = 1800,
        type_ttl_overrides: Optional[dict[MemoryType, int]] = None,
    ) -> None:
        self._default_ttl_seconds = default_ttl_seconds
        self._type_overrides: dict[MemoryType, int] = type_ttl_overrides or {
            MemoryType.CONVERSATION: 3600,
            MemoryType.DOCUMENT_CONTEXT: 7200,
            MemoryType.PATIENT_CONTEXT: 86400,
            MemoryType.PREFERENCE: 86400 * 7,
            MemoryType.TOOL: 1800,
        }

    @property
    def default_ttl_seconds(self) -> int:
        return self._default_ttl_seconds

    def get_ttl(self, memory_type: MemoryType) -> int:
        return self._type_overrides.get(memory_type, self._default_ttl_seconds)

    def is_expired(self, entry: MemoryEntry) -> bool:
        if entry.expires_at is None:
            return False
        return datetime.utcnow() > entry.expires_at

    def set_expiry(self, entry: MemoryEntry) -> MemoryEntry:
        ttl = self.get_ttl(entry.memory_type)
        entry.expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        return entry

    def filter_expired(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        return [e for e in entries if not self.is_expired(e)]

    def validate(self, entry: MemoryEntry) -> None:
        if self.is_expired(entry):
            raise ExpiryPolicyViolationError(
                f"Entry {entry.memory_id} has expired (expired at {entry.expires_at})"
            )
