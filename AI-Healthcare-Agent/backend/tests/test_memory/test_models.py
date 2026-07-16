from __future__ import annotations

from datetime import datetime, timedelta

from app.memory.models import (
    MEMORY_SCHEMA_VERSION,
    ConversationMemoryData,
    DocumentContextData,
    MemoryEntry,
    MemoryImportance,
    MemoryQuery,
    MemoryType,
    PatientContextData,
    PreferenceMemoryData,
    ToolMemoryData,
)


class TestMemoryEntry:
    def test_default_values(self) -> None:
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={"q": "test"})
        assert entry.importance == 0.5
        assert entry.importance_label == MemoryImportance.MEDIUM
        assert entry.is_expired is False

    def test_is_expired(self) -> None:
        entry = MemoryEntry(
            memory_id="m1", session_id="s1",
            memory_type=MemoryType.CONVERSATION,
            content={},
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        assert entry.is_expired is True

    def test_not_expired(self) -> None:
        entry = MemoryEntry(
            memory_id="m1", session_id="s1",
            memory_type=MemoryType.CONVERSATION,
            content={},
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        assert entry.is_expired is False

    def test_importance_high(self) -> None:
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={}, importance=0.9)
        assert entry.importance_label == MemoryImportance.HIGH

    def test_importance_low(self) -> None:
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={}, importance=0.2)
        assert entry.importance_label == MemoryImportance.LOW


class TestMemoryType:
    def test_values(self) -> None:
        assert MemoryType.CONVERSATION.value == "conversation"
        assert MemoryType.DOCUMENT_CONTEXT.value == "document_context"
        assert MemoryType.PATIENT_CONTEXT.value == "patient_context"
        assert MemoryType.PREFERENCE.value == "preference"
        assert MemoryType.TOOL.value == "tool"

    def test_all_types(self) -> None:
        assert len(MemoryType) == 5


class TestConversationMemoryData:
    def test_defaults(self) -> None:
        data = ConversationMemoryData()
        assert data.turn_number == 0
        assert data.query == ""
        assert data.follow_up is False


class TestDocumentContextData:
    def test_defaults(self) -> None:
        data = DocumentContextData()
        assert data.document_id == ""
        assert data.version == "1.0.0"
        assert data.sections == []


class TestPatientContextData:
    def test_defaults(self) -> None:
        data = PatientContextData()
        assert data.language == "en"
        assert data.notification_enabled is True
        assert data.notification_channels == ["email"]


class TestPreferenceMemoryData:
    def test_defaults(self) -> None:
        data = PreferenceMemoryData()
        assert data.preference_type == ""
        assert data.category == "general"


class TestToolMemoryData:
    def test_defaults(self) -> None:
        data = ToolMemoryData()
        assert data.tool_name == ""
        assert data.action == ""
        assert data.result == {}


class TestMemoryQuery:
    def test_defaults(self) -> None:
        query = MemoryQuery()
        assert query.session_id == ""
        assert query.limit == 20
        assert query.min_importance == 0.0
        assert query.include_expired is False


class TestSchemaVersion:
    def test_version(self) -> None:
        assert MEMORY_SCHEMA_VERSION == "1.0.0"
