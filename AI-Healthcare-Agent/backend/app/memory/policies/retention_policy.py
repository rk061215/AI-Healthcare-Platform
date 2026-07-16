from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from app.memory.exceptions import RetentionPolicyViolationError
from app.memory.models import MemoryEntry, MemoryType


class RetentionPolicy:
    def __init__(
        self,
        max_sessions_per_patient: int = 10,
        retention_days: int = 30,
    ) -> None:
        self._max_sessions_per_patient = max_sessions_per_patient
        self._retention_days = retention_days

    @property
    def max_sessions_per_patient(self) -> int:
        return self._max_sessions_per_patient

    @property
    def retention_days(self) -> int:
        return self._retention_days

    def check_retention(self, entry: MemoryEntry) -> bool:
        if entry.expires_at is not None:
            return datetime.utcnow() <= entry.expires_at
        age = datetime.utcnow() - entry.created_at
        return age.days < self._retention_days

    def can_store(self, entry: MemoryEntry) -> bool:
        if entry.memory_type == MemoryType.PATIENT_CONTEXT:
            return True
        if entry.memory_type == MemoryType.DOCUMENT_CONTEXT:
            return True
        return self.check_retention(entry)

    def filter_retention(self, entries: list[MemoryEntry]) -> list[MemoryEntry]:
        return [e for e in entries if self.check_retention(e)]

    def exceeds_session_limit(
        self,
        session_count: int,
    ) -> bool:
        return session_count >= self._max_sessions_per_patient

    def validate(self, entry: MemoryEntry) -> None:
        if not self.can_store(entry):
            raise RetentionPolicyViolationError(
                f"Entry {entry.memory_id} exceeds retention policy limits"
            )
