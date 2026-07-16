from __future__ import annotations

from typing import Any, Optional

from app.memory.base_memory import BaseMemoryStore
from app.memory.models import MemoryEntry, MemoryQuery, MemoryType
from app.memory.types.conversation_memory import ConversationMemory
from app.memory.types.document_context import DocumentContext
from app.memory.types.patient_context import PatientContext
from app.memory.types.preference_memory import PreferenceMemory
from app.memory.types.tool_memory import ToolMemory
from app.memory.policies.privacy_policy import PrivacyPolicy


class MemoryRetriever:
    def __init__(
        self,
        store: BaseMemoryStore,
        privacy_policy: Optional[PrivacyPolicy] = None,
    ) -> None:
        self._store = store
        self._privacy_policy = privacy_policy or PrivacyPolicy()
        self._conversation = ConversationMemory()
        self._document = DocumentContext()
        self._patient = PatientContext()
        self._preference = PreferenceMemory()
        self._tool = ToolMemory()

    def retrieve(
        self,
        session_id: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 20,
        min_importance: float = 0.0,
    ) -> list[MemoryEntry]:
        query = MemoryQuery(
            session_id=session_id,
            memory_type=memory_type,
            limit=limit,
            min_importance=min_importance,
        )
        results = self._store.search(query)
        if self._privacy_policy:
            results = [
                self._privacy_policy.apply(e) for e in results
            ]
        return results

    def retrieve_conversation(
        self,
        session_id: str,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        return self.retrieve(
            session_id=session_id,
            memory_type=MemoryType.CONVERSATION,
            limit=limit,
        )

    def retrieve_document_context(
        self,
        session_id: str,
    ) -> Optional[MemoryEntry]:
        results = self.retrieve(
            session_id=session_id,
            memory_type=MemoryType.DOCUMENT_CONTEXT,
            limit=1,
        )
        return results[0] if results else None

    def retrieve_patient_context(
        self,
        session_id: str,
    ) -> Optional[MemoryEntry]:
        results = self.retrieve(
            session_id=session_id,
            memory_type=MemoryType.PATIENT_CONTEXT,
            limit=1,
        )
        return results[0] if results else None

    def retrieve_preferences(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        return self.retrieve(
            session_id=session_id,
            memory_type=MemoryType.PREFERENCE,
            limit=limit,
        )

    def retrieve_tool_memory(
        self,
        session_id: str,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        return self.retrieve(
            session_id=session_id,
            memory_type=MemoryType.TOOL,
            limit=limit,
        )
