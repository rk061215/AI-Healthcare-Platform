from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional


class BaseCheckpointStore(ABC):
    @abstractmethod
    def save(self, checkpoint_id: str, state: dict[str, Any]) -> None:
        ...

    @abstractmethod
    def load(self, checkpoint_id: str) -> Optional[dict[str, Any]]:
        ...

    @abstractmethod
    def list_checkpoints(self, session_id: str) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    def delete(self, checkpoint_id: str) -> bool:
        ...

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        ...


class InMemoryCheckpointStore(BaseCheckpointStore):
    def __init__(self) -> None:
        self._checkpoints: dict[str, dict[str, Any]] = {}
        self._session_index: dict[str, list[str]] = {}

    def save(self, checkpoint_id: str, state: dict[str, Any]) -> None:
        snapshot = dict(state)
        snapshot["_saved_at"] = datetime.now(timezone.utc).isoformat()
        self._checkpoints[checkpoint_id] = snapshot
        session_id = state.get("session_id", "")
        if session_id:
            if session_id not in self._session_index:
                self._session_index[session_id] = []
            self._session_index[session_id].append(checkpoint_id)

    def load(self, checkpoint_id: str) -> Optional[dict[str, Any]]:
        return self._checkpoints.get(checkpoint_id)

    def list_checkpoints(self, session_id: str) -> list[dict[str, Any]]:
        ids = self._session_index.get(session_id, [])
        result = []
        for cid in ids:
            cp = self._checkpoints.get(cid)
            if cp:
                result.append({"checkpoint_id": cid, "saved_at": cp.get("_saved_at", "")})
        return result

    def delete(self, checkpoint_id: str) -> bool:
        if checkpoint_id in self._checkpoints:
            state = self._checkpoints.pop(checkpoint_id)
            session_id = state.get("session_id", "")
            if session_id in self._session_index:
                self._session_index[session_id] = [
                    cid for cid in self._session_index[session_id] if cid != checkpoint_id
                ]
            return True
        return False

    def health_check(self) -> dict[str, Any]:
        return {
            "provider": "in_memory",
            "checkpoint_count": len(self._checkpoints),
            "session_count": len(self._session_index),
            "healthy": True,
        }


class CheckpointManager:
    def __init__(self, store: Optional[BaseCheckpointStore] = None) -> None:
        self._store = store or InMemoryCheckpointStore()

    @property
    def store(self) -> BaseCheckpointStore:
        return self._store

    def create_checkpoint(self, state: dict[str, Any]) -> str:
        cid = uuid.uuid4().hex[:16]
        state["checkpoint_id"] = cid
        self._store.save(cid, state)
        return cid

    def restore_checkpoint(self, checkpoint_id: str) -> Optional[dict[str, Any]]:
        return self._store.load(checkpoint_id)

    def list_sessions(self, session_id: str) -> list[dict[str, Any]]:
        return self._store.list_checkpoints(session_id)

    def health_check(self) -> dict[str, Any]:
        return self._store.health_check()
