from __future__ import annotations

from typing import Any

import pytest

from app.memory.memory_service import MemoryService
from app.memory.config import MemoryConfig
from app.memory.models import MemoryType, MemoryEntry
from app.memory.exceptions import MemoryFullError, MemoryNotFoundError, SessionNotFoundError
from app.memory.stores.in_memory_store import InMemoryStore


@pytest.fixture
def memory_config() -> MemoryConfig:
    return MemoryConfig(
        provider="in_memory",
        max_memories_per_session=50,
        enable_conversation_memory=True,
        enable_expiry_policy=False,
        enable_retention_policy=False,
        enable_pruning=True,
        pruning_max_count=100,
    )


@pytest.fixture
def memory_service(memory_config) -> MemoryService:
    return MemoryService(config=memory_config)


class TestSessionLifecycle:
    def test_session_creation_tracks_existence(self, memory_service):
        session_id = "session-lifecycle-1"
        entry = memory_service.remember(
            session_id=session_id,
            content={"query": "What is my medicine?", "answer": "Lisinopril 10mg"},
            memory_type="conversation",
        )
        assert entry is not None
        assert entry.session_id == session_id
        sessions = memory_service.list_sessions()
        assert session_id in sessions

    def test_recall_returns_memories(self, memory_service):
        session_id = "session-recall-1"
        memory_service.remember(
            session_id=session_id,
            content={"query": "Q1", "answer": "A1"},
            memory_type="conversation",
        )
        memory_service.remember(
            session_id=session_id,
            content={"query": "Q2", "answer": "A2"},
            memory_type="conversation",
        )
        entries = memory_service.recall(session_id)
        assert len(entries) == 2
        contents = [e.content["query"] for e in entries]
        assert "Q1" in contents
        assert "Q2" in contents

    def test_recall_unknown_session_returns_empty(self, memory_service):
        entries = memory_service.recall("nonexistent-session")
        assert entries == []

    def test_multiple_sessions_isolated(self, memory_service):
        memory_service.remember(session_id="s1", content={"q": "q1"}, memory_type="conversation")
        memory_service.remember(session_id="s2", content={"q": "q2"}, memory_type="conversation")
        assert len(memory_service.recall("s1")) == 1
        assert len(memory_service.recall("s2")) == 1

    def test_session_count(self, memory_service):
        memory_service.remember(session_id="sc1", content={"x": "y"}, memory_type="conversation")
        memory_service.remember(session_id="sc1", content={"x": "z"}, memory_type="conversation")
        count = memory_service.get_session_count("sc1")
        assert count >= 2


class TestMemoryPersistence:
    def test_remember_returns_entry_with_id(self, memory_service):
        entry = memory_service.remember(
            session_id="s-persist-1",
            content={"query": "test"},
            memory_type="conversation",
        )
        assert entry.memory_id is not None
        assert len(entry.memory_id) > 0

    def test_remember_stores_content(self, memory_service):
        content = {"query": "What is my diagnosis?", "answer": "Hypertension"}
        entry = memory_service.remember(
            session_id="s-content-1",
            content=content,
            memory_type="conversation",
        )
        assert entry.content == content

    def test_extract_from_chat_stores_entry(self, memory_service):
        entry = memory_service.extract_from_chat(
            session_id="s-extract-1",
            query="What medicine?",
            answer="Lisinopril 10mg",
            query_type="medication",
            confidence=0.85,
            turn_number=1,
            follow_up=False,
        )
        assert entry is not None
        assert entry.memory_type == MemoryType.CONVERSATION
        entries = memory_service.recall("s-extract-1")
        assert len(entries) >= 1

    def test_extract_from_chat_tracks_turns(self, memory_service):
        for i in range(3):
            memory_service.extract_from_chat(
                session_id="s-turns-1",
                query=f"Q{i}",
                answer=f"A{i}",
                turn_number=i + 1,
            )
        entries = memory_service.recall("s-turns-1")
        assert len(entries) == 3

    def test_forget_removes_entry(self, memory_service):
        entry = memory_service.remember(
            session_id="s-forget-1",
            content={"test": "data"},
            memory_type="conversation",
        )
        result = memory_service.forget(entry.memory_id)
        assert result is True
        assert memory_service.recall("s-forget-1") == []

    def test_forget_nonexistent_raises(self, memory_service):
        with pytest.raises(MemoryNotFoundError):
            memory_service.forget("nonexistent-id")

    def test_clear_session(self, memory_service):
        for i in range(3):
            memory_service.extract_from_chat(
                session_id="s-clear-1", query=f"Q{i}", answer=f"A{i}", turn_number=i,
            )
        cleared = memory_service.clear("s-clear-1")
        assert cleared >= 3
        assert memory_service.recall("s-clear-1") == []

    def test_clear_nonexistent_raises(self, memory_service):
        with pytest.raises(SessionNotFoundError):
            memory_service.clear("nonexistent")


class TestMemoryIntegration:
    def test_remember_then_recall_full_cycle(self, memory_service):
        session_id = "s-fullcycle-1"
        memory_service.extract_from_chat(
            session_id=session_id,
            query="What is my blood pressure medicine?",
            answer="You take Lisinopril 10mg once daily.",
            query_type="medication",
            confidence=0.9,
            turn_number=1,
        )
        memory_service.extract_from_chat(
            session_id=session_id,
            query="When should I take it?",
            answer="Take it in the morning with food.",
            query_type="medication",
            confidence=0.85,
            turn_number=2,
        )
        entries = memory_service.recall(session_id)
        assert len(entries) == 2
        all_answers = " ".join(e.content["answer"] for e in entries)
        assert "Lisinopril" in all_answers
        assert "morning" in all_answers

    def test_memory_importance_tracking(self, memory_service):
        entry = memory_service.remember(
            session_id="s-import-1",
            content={"info": "critical diagnosis"},
            memory_type="conversation",
            importance=0.95,
        )
        assert entry.importance == 0.95
        assert entry.importance_label.value == "high"

    def test_memory_type_enum(self, memory_service):
        for mem_type in ["conversation", "document_context", "patient_context", "preference", "tool"]:
            entry = memory_service.remember(
                session_id="s-types-1",
                content={"type": mem_type},
                memory_type=mem_type,
            )
            assert entry.memory_type.value == mem_type

    def test_memory_with_metadata(self, memory_service):
        entry = memory_service.remember(
            session_id="s-meta-1",
            content={"query": "test"},
            memory_type="conversation",
            metadata={"source": "chat", "patient_id": "p1"},
        )
        assert entry.metadata["source"] == "chat"
        assert entry.metadata["patient_id"] == "p1"


class TestMemoryEdgeCases:
    def test_max_memories_enforced(self):
        config = MemoryConfig(
            provider="in_memory",
            max_memories_per_session=3,
            enable_pruning=False,
        )
        service = MemoryService(config=config)
        for i in range(3):
            service.remember(
                session_id="s-max-1",
                content={"i": i},
                memory_type="conversation",
            )
        with pytest.raises(MemoryFullError):
            service.remember(
                session_id="s-max-1",
                content={"i": 4},
                memory_type="conversation",
            )

    def test_pruning_removes_low_importance(self):
        config = MemoryConfig(
            provider="in_memory",
            max_memories_per_session=10,
            enable_pruning=True,
            pruning_max_count=5,
            pruning_importance_threshold=0.5,
        )
        service = MemoryService(config=config)
        for i in range(10):
            service.remember(
                session_id="s-prune-1",
                content={"i": i},
                memory_type="conversation",
                importance=0.1 if i < 5 else 0.9,
            )
        report = service.prune_session("s-prune-1")
        assert report is not None
        remaining = service.recall("s-prune-1")
        assert len(remaining) <= 5

    def test_empty_session_cleanup(self, memory_service):
        entries = memory_service.recall("s-empty-1")
        assert entries == []

    def test_large_content_storage(self, memory_service):
        large_content = {"data": "x" * 10000}
        entry = memory_service.remember(
            session_id="s-large-1",
            content=large_content,
            memory_type="conversation",
        )
        assert entry is not None
        recalled = memory_service.recall("s-large-1")
        assert len(recalled) == 1
        assert len(recalled[0].content["data"]) == 10000


class TestConversationHistoryFormatting:
    def test_memory_entries_format_as_history(self, memory_service):
        session_id = "s-format-1"
        memory_service.extract_from_chat(
            session_id=session_id, query="What is my med?", answer="Lisinopril 10mg",
            turn_number=1, query_type="medication",
        )
        memory_service.extract_from_chat(
            session_id=session_id, query="When to take?", answer="Morning with food",
            turn_number=2, query_type="medication",
        )
        entries = memory_service.recall(session_id)
        assert len(entries) >= 2
        for e in entries:
            assert "query" in e.content
            assert "answer" in e.content

    def test_memory_filter_by_type(self, memory_service):
        session_id = "s-filter-1"
        memory_service.remember(session_id=session_id, content={"q": "conv"}, memory_type="conversation")
        memory_service.remember(session_id=session_id, content={"q": "pref"}, memory_type="preference")
        conv_entries = memory_service.recall(session_id, memory_type="conversation")
        assert len(conv_entries) == 1
        assert conv_entries[0].content["q"] == "conv"

    def test_recall_with_limit(self, memory_service):
        for i in range(10):
            memory_service.extract_from_chat(
                session_id="s-limit-1", query=f"Q{i}", answer=f"A{i}", turn_number=i,
            )
        entries = memory_service.recall("s-limit-1", limit=3)
        assert len(entries) <= 3
