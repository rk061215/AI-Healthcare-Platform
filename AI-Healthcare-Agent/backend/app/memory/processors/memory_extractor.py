from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.memory.exceptions import MemoryExtractionError
from app.memory.models import MemoryEntry, MemoryType
from app.memory.types.conversation_memory import ConversationMemory
from app.memory.types.document_context import DocumentContext
from app.memory.types.patient_context import PatientContext
from app.memory.types.preference_memory import PreferenceMemory
from app.memory.types.tool_memory import ToolMemory


@dataclass
class ExtractionResult:
    entries: list[MemoryEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class MemoryExtractor:
    def __init__(self) -> None:
        self._conversation = ConversationMemory()
        self._document = DocumentContext()
        self._patient = PatientContext()
        self._preference = PreferenceMemory()
        self._tool = ToolMemory()

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
        try:
            return self._conversation.create_entry(
                session_id=session_id,
                turn_number=turn_number,
                query=query,
                answer=answer,
                query_type=query_type,
                confidence=confidence,
                follow_up=follow_up,
            )
        except Exception as e:
            raise MemoryExtractionError(f"Failed to extract conversation memory: {e}")

    def extract_from_document(
        self,
        session_id: str,
        document_id: str,
        patient_id: str,
        report_id: str = "",
        document_type: str = "",
        sections: Optional[list[str]] = None,
    ) -> MemoryEntry:
        try:
            return self._document.create_entry(
                session_id=session_id,
                document_id=document_id,
                patient_id=patient_id,
                report_id=report_id,
                document_type=document_type,
                sections=sections,
            )
        except Exception as e:
            raise MemoryExtractionError(f"Failed to extract document context: {e}")

    def extract_patient_context(
        self,
        session_id: str,
        patient_id: str,
        language: str = "en",
        preferred_doctor_id: Optional[str] = None,
    ) -> MemoryEntry:
        try:
            return self._patient.create_entry(
                session_id=session_id,
                patient_id=patient_id,
                language=language,
                preferred_doctor_id=preferred_doctor_id,
            )
        except Exception as e:
            raise MemoryExtractionError(f"Failed to extract patient context: {e}")

    def extract_preference(
        self,
        session_id: str,
        preference_type: str,
        preference_key: str,
        preference_value: Any,
        category: str = "general",
    ) -> MemoryEntry:
        try:
            return self._preference.create_entry(
                session_id=session_id,
                preference_type=preference_type,
                preference_key=preference_key,
                preference_value=preference_value,
                category=category,
            )
        except Exception as e:
            raise MemoryExtractionError(f"Failed to extract preference: {e}")

    def extract_tool_memory(
        self,
        session_id: str,
        tool_name: str,
        action: str,
        result: Optional[dict[str, Any]] = None,
    ) -> MemoryEntry:
        try:
            return self._tool.create_entry(
                session_id=session_id,
                tool_name=tool_name,
                action=action,
                result=result,
            )
        except Exception as e:
            raise MemoryExtractionError(f"Failed to extract tool memory: {e}")
