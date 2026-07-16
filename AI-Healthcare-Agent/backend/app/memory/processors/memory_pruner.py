from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from app.memory.base_memory import BaseMemoryStore
from app.memory.exceptions import MemoryPruningError
from app.memory.models import MemoryEntry, MemoryQuery, MemoryType


class PruningReport:
    def __init__(self) -> None:
        self.removed_count: int = 0
        self.retained_count: int = 0
        self.total_before: int = 0
        self.total_after: int = 0

    def __repr__(self) -> str:
        return (
            f"PruningReport(removed={self.removed_count}, "
            f"retained={self.retained_count}, "
            f"before={self.total_before}, after={self.total_after})"
        )


class MemoryPruner:
    def __init__(
        self,
        store: BaseMemoryStore,
        importance_threshold: float = 0.3,
        max_count: int = 50,
    ) -> None:
        self._store = store
        self._importance_threshold = importance_threshold
        self._max_count = max_count

    def prune_session(
        self,
        session_id: str,
        max_count: Optional[int] = None,
        importance_threshold: Optional[float] = None,
    ) -> PruningReport:
        report = PruningReport()
        try:
            query = MemoryQuery(session_id=session_id, limit=1000)
            all_entries = self._store.search(query)
            report.total_before = len(all_entries)
            report.total_after = report.total_before
            threshold = importance_threshold if importance_threshold is not None else self._importance_threshold
            maximum = max_count if max_count is not None else self._max_count
            sorted_entries = sorted(
                all_entries,
                key=lambda e: (e.importance, e.created_at),
                reverse=True,
            )
            to_remove: list[MemoryEntry] = []
            if len(sorted_entries) > maximum:
                to_remove.extend(sorted_entries[maximum:])
            for entry in sorted_entries[:maximum]:
                if entry.importance < threshold:
                    to_remove.append(entry)
            for entry in to_remove:
                if self._store.delete(entry.memory_id):
                    report.removed_count += 1
            report.total_after = report.total_before - report.removed_count
            report.retained_count = report.total_after
            return report
        except Exception as e:
            raise MemoryPruningError(f"Failed to prune session {session_id}: {e}")

    def prune_expired(
        self,
    ) -> PruningReport:
        report = PruningReport()
        try:
            sessions = self._store.list_sessions()
            for session_id in sessions:
                query = MemoryQuery(session_id=session_id, limit=1000, include_expired=True)
                entries = self._store.search(query)
                for entry in entries:
                    if entry.is_expired:
                        if self._store.delete(entry.memory_id):
                            report.removed_count += 1
            return report
        except Exception as e:
            raise MemoryPruningError(f"Failed to prune expired entries: {e}")
