from __future__ import annotations

from app.memory.models import MemoryEntry, MemoryType
from app.memory.types.conversation_memory import ConversationMemory
from app.memory.types.document_context import DocumentContext
from app.memory.types.patient_context import PatientContext
from app.memory.types.preference_memory import PreferenceMemory
from app.memory.types.tool_memory import ToolMemory


class TestConversationMemory:
    def test_create_entry(self) -> None:
        cm = ConversationMemory()
        entry = cm.create_entry(
            session_id="s1", turn_number=1,
            query="What medications?", answer="Metformin",
            query_type="medication", confidence=0.9, follow_up=False,
        )
        assert entry.memory_type == MemoryType.CONVERSATION
        assert entry.session_id == "s1"
        assert entry.content["query"] == "What medications?"
        assert entry.content["answer"] == "Metformin"
        assert entry.content["turn_number"] == 1

    def test_extract_turns(self) -> None:
        cm = ConversationMemory()
        e1 = cm.create_entry("s1", 1, "q1", "a1")
        e2 = cm.create_entry("s1", 2, "q2", "a2")
        entry_other = MemoryEntry(memory_id="x", session_id="s1", memory_type=MemoryType.DOCUMENT_CONTEXT, content={})
        turns = cm.extract_turns([e1, e2, entry_other])
        assert len(turns) == 2
        assert turns[0].query == "q1"
        assert turns[1].query == "q2"

    def test_summarize_turns(self) -> None:
        cm = ConversationMemory()
        e1 = cm.create_entry("s1", 1, "What meds?", "Metformin")
        e2 = cm.create_entry("s1", 2, "Any allergies?", "None")
        summary = cm.summarize_turns([e1, e2])
        assert "What meds?" in summary
        assert "Metformin" in summary
        assert "Any allergies?" in summary

    def test_summarize_turns_empty(self) -> None:
        cm = ConversationMemory()
        assert cm.summarize_turns([]) == ""


class TestDocumentContext:
    def test_create_entry(self) -> None:
        dc = DocumentContext()
        entry = dc.create_entry(
            session_id="s1", document_id="doc1",
            patient_id="pat1", report_id="rep1",
            document_type="lab_report", sections=["glucose", "hbA1c"],
        )
        assert entry.memory_type == MemoryType.DOCUMENT_CONTEXT
        assert entry.content["document_id"] == "doc1"
        assert entry.content["patient_id"] == "pat1"
        assert entry.content["sections"] == ["glucose", "hbA1c"]
        assert entry.importance == 0.8

    def test_get_active_document(self) -> None:
        dc = DocumentContext()
        e1 = dc.create_entry("s1", "doc1", "pat1")
        import time
        time.sleep(0.01)
        e2 = dc.create_entry("s1", "doc2", "pat1")
        active = dc.get_active_document([e1, e2])
        assert active is not None
        assert active.document_id == "doc2"  # latest

    def test_get_active_document_empty(self) -> None:
        dc = DocumentContext()
        assert dc.get_active_document([]) is None


class TestPatientContext:
    def test_create_entry(self) -> None:
        pc = PatientContext()
        entry = pc.create_entry("s1", "pat1", language="es", preferred_doctor_id="doc1")
        assert entry.memory_type == MemoryType.PATIENT_CONTEXT
        assert entry.content["patient_id"] == "pat1"
        assert entry.content["language"] == "es"
        assert entry.importance == 0.9

    def test_get_patient_context(self) -> None:
        pc = PatientContext()
        entry = pc.create_entry("s1", "pat1")
        result = pc.get_patient_context([entry])
        assert result is not None
        assert result.patient_id == "pat1"

    def test_get_patient_context_not_found(self) -> None:
        pc = PatientContext()
        e = MemoryEntry(memory_id="x", session_id="s1", memory_type=MemoryType.CONVERSATION, content={})
        assert pc.get_patient_context([e]) is None


class TestPreferenceMemory:
    def test_create_entry(self) -> None:
        pm = PreferenceMemory()
        entry = pm.create_entry("s1", "notification", "channels", ["sms", "email"], category="alerts")
        assert entry.memory_type == MemoryType.PREFERENCE
        assert entry.content["preference_key"] == "channels"
        assert entry.content["category"] == "alerts"

    def test_get_preferences(self) -> None:
        pm = PreferenceMemory()
        e1 = pm.create_entry("s1", "notification", "channels", ["email"], category="alerts")
        e2 = pm.create_entry("s1", "ui", "theme", "dark", category="display")
        prefs = pm.get_preferences([e1, e2])
        assert len(prefs) == 2
        alerts = pm.get_preferences([e1, e2], category="alerts")
        assert len(alerts) == 1

    def test_get_preferences_empty(self) -> None:
        pm = PreferenceMemory()
        assert pm.get_preferences([]) == []


class TestToolMemory:
    def test_create_entry(self) -> None:
        tm = ToolMemory()
        entry = tm.create_entry("s1", "appointment", "booked", {"date": "2026-07-20"})
        assert entry.memory_type == MemoryType.TOOL
        assert entry.content["tool_name"] == "appointment"
        assert entry.content["result"] == {"date": "2026-07-20"}

    def test_get_last_action(self) -> None:
        tm = ToolMemory()
        e1 = tm.create_entry("s1", "appointment", "booked", {"date": "2026-07-20"})
        e2 = tm.create_entry("s1", "reminder", "sent", {"type": "medication"})
        e3 = tm.create_entry("s1", "appointment", "cancelled", {"date": "2026-07-20"})
        last = tm.get_last_action([e1, e2, e3], "appointment")
        assert last is not None
        assert last.action == "cancelled"

    def test_get_last_action_not_found(self) -> None:
        tm = ToolMemory()
        assert tm.get_last_action([], "nonexistent") is None
