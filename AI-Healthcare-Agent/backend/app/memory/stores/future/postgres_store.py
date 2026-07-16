from __future__ import annotations

from typing import Any, Optional

from app.memory.base_memory import BaseMemoryStore
from app.memory.models import MemoryEntry, MemoryQuery


class PostgresStore(BaseMemoryStore):
    def __init__(self) -> None:
        raise NotImplementedError(
            "PostgresStore is a future provider. "
            "Install asyncpg/psycopg and implement the interface."
        )

    def store(self, entry: MemoryEntry) -> str:
        raise NotImplementedError

    def retrieve(self, memory_id: str) -> Optional[MemoryEntry]:
        raise NotImplementedError

    def search(self, query: MemoryQuery) -> list[MemoryEntry]:
        raise NotImplementedError

    def update(self, entry: MemoryEntry) -> bool:
        raise NotImplementedError

    def delete(self, memory_id: str) -> bool:
        raise NotImplementedError

    def clear_session(self, session_id: str) -> int:
        raise NotImplementedError

    def count(self, session_id: str) -> int:
        raise NotImplementedError

    def list_sessions(self) -> list[str]:
        raise NotImplementedError

    def health_check(self) -> bool:
        raise NotImplementedError
