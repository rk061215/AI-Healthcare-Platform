from __future__ import annotations

from datetime import datetime, timedelta

from app.memory.models import MemoryEntry, MemoryQuery, MemoryType
from app.memory.stores.in_memory_store import InMemoryStore


class TestInMemoryStore:
    def test_store_and_retrieve(self) -> None:
        store = InMemoryStore()
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={"q": "test"})
        stored_id = store.store(entry)
        retrieved = store.retrieve(stored_id)
        assert retrieved is not None
        assert retrieved.memory_id == stored_id
        assert retrieved.content == {"q": "test"}

    def test_store_auto_id(self) -> None:
        store = InMemoryStore()
        entry = MemoryEntry(memory_id="", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        stored_id = store.store(entry)
        assert stored_id != ""

    def test_retrieve_not_found(self) -> None:
        store = InMemoryStore()
        assert store.retrieve("nonexistent") is None

    def test_search_by_session(self) -> None:
        store = InMemoryStore()
        e1 = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        e2 = MemoryEntry(memory_id="m2", session_id="s2", memory_type=MemoryType.CONVERSATION, content={})
        store.store(e1)
        store.store(e2)
        results = store.search(MemoryQuery(session_id="s1"))
        assert len(results) == 1

    def test_search_by_type(self) -> None:
        store = InMemoryStore()
        e1 = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        e2 = MemoryEntry(memory_id="m2", session_id="s1", memory_type=MemoryType.DOCUMENT_CONTEXT, content={})
        store.store(e1)
        store.store(e2)
        results = store.search(MemoryQuery(session_id="s1", memory_type=MemoryType.CONVERSATION))
        assert len(results) == 1
        assert results[0].memory_type == MemoryType.CONVERSATION

    def test_search_expired_excluded(self) -> None:
        store = InMemoryStore()
        expired = MemoryEntry(
            memory_id="m1", session_id="s1",
            memory_type=MemoryType.CONVERSATION, content={},
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        active = MemoryEntry(
            memory_id="m2", session_id="s1",
            memory_type=MemoryType.CONVERSATION, content={},
        )
        store.store(expired)
        store.store(active)
        results = store.search(MemoryQuery(session_id="s1"))
        assert len(results) == 1

    def test_search_include_expired(self) -> None:
        store = InMemoryStore()
        expired = MemoryEntry(
            memory_id="m1", session_id="s1",
            memory_type=MemoryType.CONVERSATION, content={},
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        store.store(expired)
        results = store.search(MemoryQuery(session_id="s1", include_expired=True))
        assert len(results) == 1

    def test_search_min_importance(self) -> None:
        store = InMemoryStore()
        e1 = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={}, importance=0.8)
        e2 = MemoryEntry(memory_id="m2", session_id="s1", memory_type=MemoryType.CONVERSATION, content={}, importance=0.2)
        store.store(e1)
        store.store(e2)
        results = store.search(MemoryQuery(session_id="s1", min_importance=0.5))
        assert len(results) == 1

    def test_search_limit(self) -> None:
        store = InMemoryStore()
        for i in range(10):
            e = MemoryEntry(memory_id=f"m{i}", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
            store.store(e)
        results = store.search(MemoryQuery(session_id="s1", limit=3))
        assert len(results) == 3

    def test_update(self) -> None:
        store = InMemoryStore()
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={"q": "old"})
        store.store(entry)
        entry.content = {"q": "new"}
        assert store.update(entry) is True
        retrieved = store.retrieve("m1")
        assert retrieved is not None
        assert retrieved.content == {"q": "new"}

    def test_update_not_found(self) -> None:
        store = InMemoryStore()
        entry = MemoryEntry(memory_id="nonexistent", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        assert store.update(entry) is False

    def test_delete(self) -> None:
        store = InMemoryStore()
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        store.store(entry)
        assert store.delete("m1") is True
        assert store.retrieve("m1") is None

    def test_delete_not_found(self) -> None:
        store = InMemoryStore()
        assert store.delete("nonexistent") is False

    def test_clear_session(self) -> None:
        store = InMemoryStore()
        for i in range(3):
            e = MemoryEntry(memory_id=f"m{i}", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
            store.store(e)
        assert store.clear_session("s1") == 3
        assert store.count("s1") == 0

    def test_clear_session_partial(self) -> None:
        store = InMemoryStore()
        e1 = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        e2 = MemoryEntry(memory_id="m2", session_id="s2", memory_type=MemoryType.CONVERSATION, content={})
        store.store(e1)
        store.store(e2)
        assert store.clear_session("s1") == 1

    def test_count(self) -> None:
        store = InMemoryStore()
        assert store.count("s1") == 0
        e = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        store.store(e)
        assert store.count("s1") == 1

    def test_list_sessions(self) -> None:
        store = InMemoryStore()
        e1 = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        e2 = MemoryEntry(memory_id="m2", session_id="s2", memory_type=MemoryType.CONVERSATION, content={})
        store.store(e1)
        store.store(e2)
        sessions = store.list_sessions()
        assert "s1" in sessions
        assert "s2" in sessions

    def test_health_check(self) -> None:
        store = InMemoryStore()
        assert store.health_check() is True

    def test_deep_copy_on_store(self) -> None:
        store = InMemoryStore()
        entry = MemoryEntry(memory_id="m1", session_id="s1", memory_type=MemoryType.CONVERSATION, content={"key": "val"})
        store.store(entry)
        entry.content["key"] = "modified"
        retrieved = store.retrieve("m1")
        assert retrieved is not None
        assert retrieved.content["key"] == "val"
