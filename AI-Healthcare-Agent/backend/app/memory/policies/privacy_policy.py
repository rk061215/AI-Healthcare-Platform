from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.memory.exceptions import PrivacyPolicyViolationError
from app.memory.models import MemoryEntry


class PrivacyPolicy:
    def __init__(
        self,
        allowed_fields: tuple[str, ...] = (
            "query", "answer", "memory_type", "memory_id",
            "session_id", "created_at", "importance",
        ),
        restricted_fields: tuple[str, ...] = (
            "patient_id", "doctor_id", "report_id",
            "personal_info", "contact_info",
        ),
        strict_mode: bool = False,
    ) -> None:
        self._allowed_fields = allowed_fields
        self._restricted_fields = restricted_fields
        self._strict_mode = strict_mode

    @property
    def allowed_fields(self) -> tuple[str, ...]:
        return self._allowed_fields

    @property
    def restricted_fields(self) -> tuple[str, ...]:
        return self._restricted_fields

    def apply(self, entry: MemoryEntry) -> MemoryEntry:
        if not self._strict_mode:
            return entry
        sanitized = deepcopy(entry)
        sanitized.content = self._sanitize_dict(sanitized.content)
        sanitized.metadata = self._sanitize_dict(sanitized.metadata)
        return sanitized

    def check_field_access(self, field_name: str) -> bool:
        if field_name in self._restricted_fields:
            return False
        if self._allowed_fields and field_name not in self._allowed_fields:
            return False
        return True

    def validate_access(self, entry: MemoryEntry) -> None:
        if not self._strict_mode:
            return
        restricted = [
            k for k in entry.content
            if k in self._restricted_fields
        ]
        if restricted:
            raise PrivacyPolicyViolationError(
                f"Access to restricted fields denied: {restricted}"
            )

    def _sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            k: v for k, v in data.items()
            if k not in self._restricted_fields
        }
