from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

MEMORY_SCHEMA_VERSION = "1.0.0"


class MemoryType(str, Enum):
    CONVERSATION = "conversation"
    DOCUMENT_CONTEXT = "document_context"
    PATIENT_CONTEXT = "patient_context"
    PREFERENCE = "preference"
    TOOL = "tool"


class MemoryImportance(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MemoryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    memory_id: str
    session_id: str
    memory_type: MemoryType
    content: dict[str, Any]
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def importance_label(self) -> MemoryImportance:
        if self.importance >= 0.7:
            return MemoryImportance.HIGH
        elif self.importance >= 0.4:
            return MemoryImportance.MEDIUM
        return MemoryImportance.LOW


class ConversationMemoryData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_number: int = 0
    query: str = ""
    answer: str = ""
    query_type: str = "unknown"
    confidence: float = 0.0
    follow_up: bool = False


class DocumentContextData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str = ""
    patient_id: str = ""
    report_id: str = ""
    document_type: str = ""
    version: str = "1.0.0"
    upload_timestamp: Optional[datetime] = None
    sections: list[str] = Field(default_factory=list)


class PatientContextData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: str = ""
    language: str = "en"
    preferred_doctor_id: Optional[str] = None
    notification_enabled: bool = True
    notification_channels: list[str] = Field(default_factory=lambda: ["email"])
    timezone: str = "UTC"


class PreferenceMemoryData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preference_type: str = ""
    preference_key: str = ""
    preference_value: Any = None
    category: str = "general"


class ToolMemoryData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_name: str = ""
    action: str = ""
    result: dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = None


class MemorySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    memory_type: MemoryType
    summary_text: str
    entry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class MemoryQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = ""
    memory_type: Optional[MemoryType] = None
    limit: int = 20
    min_importance: float = 0.0
    include_expired: bool = False
    time_range_hours: Optional[int] = None
