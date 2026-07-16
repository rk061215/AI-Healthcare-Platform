from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.memory.models import MemoryEntry, MemoryQuery


class BaseMemoryStore(ABC):
    @abstractmethod
    def store(self, entry: MemoryEntry) -> str:
        ...

    @abstractmethod
    def retrieve(self, memory_id: str) -> Optional[MemoryEntry]:
        ...

    @abstractmethod
    def search(self, query: MemoryQuery) -> list[MemoryEntry]:
        ...

    @abstractmethod
    def update(self, entry: MemoryEntry) -> bool:
        ...

    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        ...

    @abstractmethod
    def clear_session(self, session_id: str) -> int:
        ...

    @abstractmethod
    def count(self, session_id: str) -> int:
        ...

    @abstractmethod
    def list_sessions(self) -> list[str]:
        ...

    @abstractmethod
    def health_check(self) -> bool:
        ...


class BaseMemory(ABC):
    @abstractmethod
    def remember(
        self,
        session_id: str,
        content: dict[str, Any],
        memory_type: str,
        importance: float = 0.5,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MemoryEntry:
        ...

    @abstractmethod
    def recall(
        self,
        session_id: str,
        memory_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        ...

    @abstractmethod
    def forget(self, memory_id: str) -> bool:
        ...

    @abstractmethod
    def clear(self, session_id: str) -> int:
        ...
