from __future__ import annotations

from typing import Any, Optional
from uuid import uuid4

from app.memory.base_memory import BaseMemory, BaseMemoryStore
from app.memory.config import MemoryConfig
from app.memory.exceptions import (
    MemoryFullError,
    MemoryNotFoundError,
    SessionNotFoundError,
)
from app.memory.memory_factory import MemoryFactory
from app.memory.models import MemoryEntry, MemoryQuery, MemoryType
from app.memory.policies.expiry_policy import ExpiryPolicy
from app.memory.policies.privacy_policy import PrivacyPolicy
from app.memory.policies.retention_policy import RetentionPolicy
from app.memory.processors.memory_extractor import MemoryExtractor
from app.memory.processors.memory_pruner import MemoryPruner, PruningReport
from app.memory.processors.memory_retriever import MemoryRetriever
from app.memory.processors.memory_summarizer import MemorySummarizer, SummarizationResult


class MemoryService(BaseMemory):
    def __init__(
        self,
        store: Optional[BaseMemoryStore] = None,
        config: Optional[MemoryConfig] = None,
    ) -> None:
        self._config = config or MemoryConfig()
        self._store = store or MemoryFactory.create(self._config.provider)
        self._retention = RetentionPolicy(
            max_sessions_per_patient=self._config.max_sessions_per_patient,
            retention_days=self._config.retention_days,
        )
        self._privacy = PrivacyPolicy(
            allowed_fields=self._config.privacy_allowed_fields,
            restricted_fields=self._config.privacy_restricted_fields,
        )
        self._expiry = ExpiryPolicy(
            default_ttl_seconds=self._config.default_ttl_seconds,
        )
        self._extractor = MemoryExtractor()
        self._retriever = MemoryRetriever(store=self._store, privacy_policy=self._privacy)
        self._summarizer = MemorySummarizer(store=self._store)
        self._pruner = MemoryPruner(
            store=self._store,
            importance_threshold=self._config.pruning_importance_threshold,
            max_count=self._config.pruning_max_count,
        )

    @property
    def store(self) -> BaseMemoryStore:
        return self._store

    @property
    def config(self) -> MemoryConfig:
        return self._config

    @property
    def extractor(self) -> MemoryExtractor:
        return self._extractor

    @property
    def retriever(self) -> MemoryRetriever:
        return self._retriever

    @property
    def summarizer(self) -> MemorySummarizer:
        return self._summarizer

    @property
    def pruner(self) -> MemoryPruner:
        return self._pruner

    @property
    def retention_policy(self) -> RetentionPolicy:
        return self._retention

    @property
    def privacy_policy(self) -> PrivacyPolicy:
        return self._privacy

    @property
    def expiry_policy(self) -> ExpiryPolicy:
        return self._expiry

    def remember(
        self,
        session_id: str,
        content: dict[str, Any],
        memory_type: str,
        importance: float = 0.5,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MemoryEntry:
        memory_type_enum = MemoryType(memory_type)
        if self._config.max_memories_per_session > 0:
            current_count = self._store.count(session_id)
            if current_count >= self._config.max_memories_per_session:
                if self._config.enable_pruning:
                    self._pruner.prune_session(session_id)
                    if self._store.count(session_id) >= self._config.max_memories_per_session:
                        raise MemoryFullError(
                            f"Session {session_id} has reached maximum memories "
                            f"({self._config.max_memories_per_session})"
                        )
                else:
                    raise MemoryFullError(
                        f"Session {session_id} has reached maximum memories "
                        f"({self._config.max_memories_per_session})"
                    )
        entry = MemoryEntry(
            memory_id=str(uuid4()),
            session_id=session_id,
            memory_type=memory_type_enum,
            content=content,
            importance=importance,
            metadata=metadata or {},
        )
        if self._config.enable_expiry_policy:
            entry = self._expiry.set_expiry(entry)
        if self._config.enable_retention_policy:
            self._retention.validate(entry)
        self._store.store(entry)
        return entry

    def recall(
        self,
        session_id: str,
        memory_type: Optional[str] = None,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        if session_id not in self._store.list_sessions():
            return []
        mt = MemoryType(memory_type) if memory_type else None
        results = self._retriever.retrieve(
            session_id=session_id,
            memory_type=mt,
            limit=limit,
        )
        if self._config.enable_retention_policy:
            results = self._retention.filter_retention(results)
        if self._config.enable_expiry_policy:
            results = self._expiry.filter_expired(results)
        return results

    def forget(self, memory_id: str) -> bool:
        result = self._store.delete(memory_id)
        if not result:
            raise MemoryNotFoundError(f"Memory entry '{memory_id}' not found")
        return True

    def clear(self, session_id: str) -> int:
        if session_id not in self._store.list_sessions():
            raise SessionNotFoundError(f"Session '{session_id}' not found")
        return self._store.clear_session(session_id)

    def extract_from_chat(
        self,
        session_id: str,
        query: str,
        answer: str,
        query_type: str = "unknown",
        confidence: float = 0.0,
        turn_number: int = 0,
        follow_up: bool = False,
    ) -> MemoryEntry:
        if not self._config.enable_conversation_memory:
            raise MemoryNotFoundError("Conversation memory is disabled")
        entry = self._extractor.extract_from_chat(
            session_id=session_id,
            query=query,
            answer=answer,
            query_type=query_type,
            confidence=confidence,
            turn_number=turn_number,
            follow_up=follow_up,
        )
        return self.remember(
            session_id=session_id,
            content=entry.content,
            memory_type=entry.memory_type.value,
            importance=entry.importance,
            metadata=entry.metadata,
        )

    def summarize_session(self, session_id: str) -> SummarizationResult:
        return self._summarizer.summarize_conversation(
            session_id=session_id,
            max_turns=self._config.summarization_threshold,
        )

    def prune_session(self, session_id: str) -> PruningReport:
        return self._pruner.prune_session(
            session_id=session_id,
            max_count=self._config.pruning_max_count,
            importance_threshold=self._config.pruning_importance_threshold,
        )

    def prune_expired(self) -> PruningReport:
        return self._pruner.prune_expired()

    def list_sessions(self) -> list[str]:
        return self._store.list_sessions()

    def get_session_count(self, session_id: str) -> int:
        return self._store.count(session_id)
