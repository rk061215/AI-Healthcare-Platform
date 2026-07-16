from __future__ import annotations

import copy
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from app.memory.base_memory import BaseMemoryStore
from app.memory.exceptions import MemoryNotFoundError, MemoryStoreError
from app.memory.models import MemoryEntry, MemoryQuery, MemoryType


class InMemoryStore(BaseMemoryStore):
    def __init__(self) -> None:
        self._store: dict[str, MemoryEntry] = {}
        self._session_index: dict[str, set[str]] = {}

    def store(self, entry: MemoryEntry) -> str:
        if not entry.memory_id:
            entry.memory_id = str(uuid.uuid4())
        self._store[entry.memory_id] = copy.deepcopy(entry)
        if entry.session_id not in self._session_index:
            self._session_index[entry.session_id] = set()
        self._session_index[entry.session_id].add(entry.memory_id)
        return entry.memory_id

    def retrieve(self, memory_id: str) -> Optional[MemoryEntry]:
        entry = self._store.get(memory_id)
        if entry is None:
            return None
        return copy.deepcopy(entry)

    def search(self, query: MemoryQuery) -> list[MemoryEntry]:
        results: list[MemoryEntry] = []
        for entry in self._store.values():
            if query.session_id and entry.session_id != query.session_id:
                continue
            if query.memory_type and entry.memory_type != query.memory_type:
                continue
            if not query.include_expired and entry.is_expired:
                continue
            if entry.importance < query.min_importance:
                continue
            if query.time_range_hours is not None:
                cutoff = datetime.utcnow() - timedelta(hours=query.time_range_hours)
                if entry.created_at < cutoff:
                    continue
            results.append(copy.deepcopy(entry))
        results.sort(key=lambda e: e.created_at, reverse=True)
        return results[:query.limit]

    def update(self, entry: MemoryEntry) -> bool:
        if entry.memory_id not in self._store:
            return False
        entry.updated_at = datetime.utcnow()
        self._store[entry.memory_id] = copy.deepcopy(entry)
        return True

    def delete(self, memory_id: str) -> bool:
        entry = self._store.pop(memory_id, None)
        if entry is None:
            return False
        session_set = self._session_index.get(entry.session_id)
        if session_set:
            session_set.discard(memory_id)
            if not session_set:
                del self._session_index[entry.session_id]
        return True

    def clear_session(self, session_id: str) -> int:
        memory_ids = self._session_index.pop(session_id, set())
        count = 0
        for mid in memory_ids:
            if mid in self._store:
                del self._store[mid]
                count += 1
        return count

    def count(self, session_id: str) -> int:
        return len(self._session_index.get(session_id, set()))

    def list_sessions(self) -> list[str]:
        return list(self._session_index.keys())

    def health_check(self) -> bool:
        return True
