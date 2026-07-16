from __future__ import annotations

from app.langgraph.graph_checkpoint import CheckpointManager, InMemoryCheckpointStore


class TestInMemoryCheckpointStore:
    def test_save_and_load(self):
        store = InMemoryCheckpointStore()
        store.save("cp_1", {"query": "test", "session_id": "sess_1"})
        loaded = store.load("cp_1")
        assert loaded is not None
        assert loaded["query"] == "test"
        assert loaded["_saved_at"] is not None

    def test_load_missing(self):
        store = InMemoryCheckpointStore()
        loaded = store.load("nonexistent")
        assert loaded is None

    def test_list_checkpoints(self):
        store = InMemoryCheckpointStore()
        store.save("cp_1", {"session_id": "sess_1"})
        store.save("cp_2", {"session_id": "sess_1"})
        checkpoints = store.list_checkpoints("sess_1")
        assert len(checkpoints) == 2
        ids = [c["checkpoint_id"] for c in checkpoints]
        assert "cp_1" in ids
        assert "cp_2" in ids

    def test_delete_checkpoint(self):
        store = InMemoryCheckpointStore()
        store.save("cp_1", {"session_id": "sess_1"})
        deleted = store.delete("cp_1")
        assert deleted is True
        assert store.load("cp_1") is None
        assert len(store.list_checkpoints("sess_1")) == 0

    def test_delete_nonexistent(self):
        store = InMemoryCheckpointStore()
        deleted = store.delete("nonexistent")
        assert deleted is False

    def test_health_check(self):
        store = InMemoryCheckpointStore()
        health = store.health_check()
        assert health["provider"] == "in_memory"
        assert health["healthy"] is True
        assert health["checkpoint_count"] == 0

    def test_empty_session_index(self):
        store = InMemoryCheckpointStore()
        checkpoints = store.list_checkpoints("nonexistent_session")
        assert checkpoints == []


class TestCheckpointManager:
    def test_create_checkpoint(self):
        mgr = CheckpointManager()
        cid = mgr.create_checkpoint({"query": "test", "session_id": "sess_1"})
        assert cid is not None
        assert len(cid) > 0

    def test_restore_checkpoint(self):
        mgr = CheckpointManager()
        cid = mgr.create_checkpoint({"query": "test", "session_id": "sess_1"})
        restored = mgr.restore_checkpoint(cid)
        assert restored["query"] == "test"

    def test_list_sessions(self):
        mgr = CheckpointManager()
        mgr.create_checkpoint({"query": "q1", "session_id": "sess_1"})
        mgr.create_checkpoint({"query": "q2", "session_id": "sess_1"})
        mgr.create_checkpoint({"query": "q3", "session_id": "sess_2"})
        sess1 = mgr.list_sessions("sess_1")
        sess2 = mgr.list_sessions("sess_2")
        assert len(sess1) == 2
        assert len(sess2) == 1

    def test_checkpoint_id_in_state(self):
        mgr = CheckpointManager()
        state = {"query": "test", "session_id": "sess_1"}
        cid = mgr.create_checkpoint(state)
        assert state["checkpoint_id"] == cid

    def test_health_check(self):
        mgr = CheckpointManager()
        health = mgr.health_check()
        assert health["healthy"] is True

    def test_custom_store(self):
        custom_store = InMemoryCheckpointStore()
        mgr = CheckpointManager(store=custom_store)
        assert mgr.store is custom_store
