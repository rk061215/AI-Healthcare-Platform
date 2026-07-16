from __future__ import annotations

from app.agents.agent_context import AgentContext


class TestAgentContext:
    def test_default_creation(self) -> None:
        context = AgentContext(query="test", session_id="s1")
        assert context.query == "test"
        assert context.session_id == "s1"
        assert context.patient_id == ""
        assert context.document_sections == []
        assert context.memory_entries == []
        assert context.retrieved_evidence == []
        assert context.metadata == {}
        assert context.config_overrides == {}

    def test_full_context(self) -> None:
        context = AgentContext(
            query="What meds?",
            session_id="s1",
            patient_id="pat1",
            document_id="doc1",
            report_id="rep1",
            document_type="lab_report",
            document_sections=["diagnosis", "medication"],
            memory_entries=[{"key": "value"}],
            retrieved_evidence=[{"chunk": "text"}],
            active_document="doc1.pdf",
            language="fr",
            metadata={"source": "web"},
            config_overrides={"temperature": 0.5},
        )
        assert context.patient_id == "pat1"
        assert context.document_id == "doc1"
        assert "medication" in context.document_sections
        assert len(context.memory_entries) == 1
        assert context.language == "fr"

    def test_mutable_sections(self) -> None:
        context = AgentContext(query="q", session_id="s1")
        context.document_sections.append("new_section")
        assert len(context.document_sections) == 1

    def test_mutable_metadata(self) -> None:
        context = AgentContext(query="q", session_id="s1")
        context.metadata["key"] = "value"
        assert context.metadata["key"] == "value"

    def test_repr(self) -> None:
        context = AgentContext(query="test", session_id="s1")
        assert "test" in repr(context)
