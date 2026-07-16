from __future__ import annotations

import pytest

from app.memory.config import MemoryConfig
from app.memory.exceptions import (
    MemoryFullError,
    MemoryNotFoundError,
    SessionNotFoundError,
)
from app.memory.memory_service import MemoryService
from app.memory.models import MemoryEntry, MemoryType


class TestMemoryService:
    def test_remember_and_recall(self) -> None:
        service = MemoryService()
        entry = service.remember(
            session_id="s1",
            content={"query": "test", "answer": "response"},
            memory_type="conversation",
            importance=0.5,
        )
        assert entry.session_id == "s1"
        assert entry.memory_type == MemoryType.CONVERSATION
        assert entry.importance == 0.5
        recalled = service.recall("s1")
        assert len(recalled) == 1

    def test_remember_sets_expiry(self) -> None:
        config = MemoryConfig(enable_expiry_policy=True, default_ttl_seconds=3600)
        service = MemoryService(config=config)
        entry = service.remember("s1", {}, "conversation")
        assert entry.expires_at is not None

    def test_recall_nonexistent_session(self) -> None:
        service = MemoryService()
        assert service.recall("nonexistent") == []

    def test_forget(self) -> None:
        service = MemoryService()
        entry = service.remember("s1", {}, "conversation")
        assert service.forget(entry.memory_id) is True

    def test_forget_not_found(self) -> None:
        service = MemoryService()
        with pytest.raises(MemoryNotFoundError):
            service.forget("nonexistent")

    def test_clear(self) -> None:
        service = MemoryService()
        service.remember("s1", {}, "conversation")
        service.remember("s1", {}, "conversation")
        assert service.clear("s1") == 2

    def test_clear_nonexistent(self) -> None:
        service = MemoryService()
        with pytest.raises(SessionNotFoundError):
            service.clear("nonexistent")

    def test_extract_from_chat(self) -> None:
        service = MemoryService()
        entry = service.extract_from_chat(
            session_id="s1", query="What meds?", answer="Metformin",
            query_type="medication", confidence=0.9, turn_number=1,
        )
        assert entry.content["query"] == "What meds?"
        assert entry.content["answer"] == "Metformin"

    def test_extract_from_chat_disabled(self) -> None:
        config = MemoryConfig(enable_conversation_memory=False)
        service = MemoryService(config=config)
        with pytest.raises(MemoryNotFoundError):
            service.extract_from_chat("s1", "q", "a")

    def test_memory_full_with_pruning(self) -> None:
        config = MemoryConfig(max_memories_per_session=3, enable_pruning=True)
        service = MemoryService(config=config)
        for i in range(5):
            service.remember(f"s1", {"q": f"q{i}"}, "conversation", importance=0.1)
        assert service.get_session_count("s1") <= 3

    def test_memory_full_without_pruning(self) -> None:
        config = MemoryConfig(max_memories_per_session=2, enable_pruning=False)
        service = MemoryService(config=config)
        service.remember("s1", {}, "conversation")
        service.remember("s1", {}, "conversation")
        with pytest.raises(MemoryFullError):
            service.remember("s1", {}, "conversation")

    def test_summarize_session(self) -> None:
        service = MemoryService()
        service.extract_from_chat("s1", "q1", "a1", turn_number=1)
        service.extract_from_chat("s1", "q2", "a2", turn_number=2)
        result = service.summarize_session("s1")
        assert result.entries_consumed == 2
        assert "q1" in result.summary_text

    def test_prune_session(self) -> None:
        service = MemoryService()
        for i in range(10):
            service.remember("s1", {}, "conversation", importance=0.1)
        report = service.prune_session("s1")
        assert report.removed_count > 0

    def test_list_sessions(self) -> None:
        service = MemoryService()
        service.remember("s_a", {}, "conversation")
        service.remember("s_b", {}, "conversation")
        sessions = service.list_sessions()
        assert "s_a" in sessions
        assert "s_b" in sessions

    def test_get_session_count(self) -> None:
        service = MemoryService()
        assert service.get_session_count("s1") == 0
        service.remember("s1", {}, "conversation")
        assert service.get_session_count("s1") == 1

    def test_multi_turn_conversation(self) -> None:
        service = MemoryService()
        for i in range(3):
            service.extract_from_chat(
                "s1", f"q{i}", f"a{i}",
                query_type="general",
                turn_number=i,
            )
        recalled = service.recall("s1", memory_type="conversation")
        assert len(recalled) == 3
        assert recalled[0].content["turn_number"] == 2  # most recent first

    def test_different_memory_types(self) -> None:
        service = MemoryService()
        service.remember("s1", {"q": "chat"}, "conversation")
        service.remember("s1", {"doc_id": "doc1"}, "document_context")
        service.remember("s1", {"pat_id": "pat1"}, "patient_context")
        conv = service.recall("s1", memory_type="conversation")
        assert len(conv) == 1
        doc = service.recall("s1", memory_type="document_context")
        assert len(doc) == 1
        pat = service.recall("s1", memory_type="patient_context")
        assert len(pat) == 1

    def test_recall_with_importance_filter(self) -> None:
        service = MemoryService()
        service.remember("s1", {}, "conversation", importance=0.9)
        service.remember("s1", {}, "conversation", importance=0.1)
        all_mem = service.recall("s1", memory_type="conversation")
        assert len(all_mem) == 2

    def test_remember_after_clear(self) -> None:
        service = MemoryService()
        service.remember("s1", {}, "conversation")
        service.clear("s1")
        assert service.get_session_count("s1") == 0
        service.remember("s1", {}, "conversation")
        assert service.get_session_count("s1") == 1

    def test_properties(self) -> None:
        service = MemoryService()
        assert service.store is not None
        assert service.config is not None
        assert service.extractor is not None
        assert service.retriever is not None
        assert service.summarizer is not None
        assert service.pruner is not None
        assert service.retention_policy is not None
        assert service.privacy_policy is not None
        assert service.expiry_policy is not None

    def test_prune_expired(self) -> None:
        from datetime import datetime, timedelta
        config = MemoryConfig(enable_expiry_policy=False)
        service = MemoryService(config=config)
        entry = MemoryEntry(
            memory_id="expired",
            session_id="s1",
            memory_type=MemoryType.CONVERSATION,
            content={},
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        service.store.store(entry)
        report = service.prune_expired()
        assert report.removed_count == 1
