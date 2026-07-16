from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MemoryConfig:
    provider: str = "in_memory"
    default_ttl_seconds: int = 1800
    max_memories_per_session: int = 100
    max_conversation_turns: int = 50
    summarization_threshold: int = 20
    pruning_importance_threshold: float = 0.3
    pruning_max_count: int = 50
    enable_conversation_memory: bool = True
    enable_document_context: bool = True
    enable_patient_context: bool = True
    enable_preference_memory: bool = True
    enable_tool_memory: bool = True
    enable_extraction: bool = True
    enable_summarization: bool = True
    enable_pruning: bool = True
    enable_retention_policy: bool = True
    enable_privacy_policy: bool = True
    enable_expiry_policy: bool = True
    retention_days: int = 30
    max_sessions_per_patient: int = 10
    privacy_allowed_fields: tuple[str, ...] = (
        "query", "answer", "memory_type", "memory_id",
        "session_id", "created_at", "importance",
    )
    privacy_restricted_fields: tuple[str, ...] = (
        "patient_id", "doctor_id", "report_id",
        "personal_info", "contact_info",
    )

    def __post_init__(self) -> None:
        if self.max_memories_per_session < 1:
            self.max_memories_per_session = 100
