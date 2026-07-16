from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.chat.chat_service import ChatService
from app.chat.models import ChatRequest
from app.database.enums import ReportStatus
from app.models.report import Report
from app.rag.models import RAGResponse
from app.memory.memory_service import MemoryService
from app.memory.config import MemoryConfig
from app.tools.tool_service import ToolService


class TestEndToEndScenario1:
    """Scenario 1: Upload prescription, ask about medicines, get grounded answer."""

    def test_scenario1_upload_and_query(self, db_session, client, patient_token):
        with patch("app.chat.chat_service.RAGEngine") as mock_rag_cls, \
             patch("app.chat.chat_service.ConfidenceCalculator") as mock_conf_cls:
            mock_rag = MagicMock()
            mock_rag.answer.return_value = RAGResponse(
                answer="You are prescribed Lisinopril 10mg once daily and Amlodipine 5mg once daily.",
                query_type="medication",
            )
            mock_rag_cls.return_value = mock_rag
            mock_conf = MagicMock()
            from app.chat.models import ConfidenceScore, ConfidenceLevel
            mock_conf.calculate.return_value = ConfidenceScore(
                overall=0.85,
                level=ConfidenceLevel.high,
                retrieval_score=0.85,
                chunk_count=2,
                citation_coverage=0.5,
                guardrail_validated=True,
                insufficient_evidence=False,
            )
            mock_conf_cls.return_value = mock_conf
            service = ChatService()
            response = service.ask(ChatRequest(
                query="What medicines are prescribed?",
                session_id="e2e-s1",
            ))
            assert response.answer
            assert "Lisinopril" in response.answer


class TestEndToEndScenario2:
    """Scenario 2: Follow-up question tests conversation memory."""

    def test_scenario2_follow_up_with_memory(self):
        memory_service = MemoryService(config=MemoryConfig(
            provider="in_memory",
            max_memories_per_session=50,
            enable_expiry_policy=False,
            enable_retention_policy=False,
        ))
        session_id = "e2e-s2-followup"
        memory_service.extract_from_chat(
            session_id=session_id,
            query="What medicines are prescribed?",
            answer="You take Lisinopril 10mg and Amlodipine 5mg.",
            query_type="medication",
            confidence=0.9,
            turn_number=1,
        )
        entries = memory_service.recall(session_id)
        assert len(entries) == 1
        assert "Lisinopril" in entries[0].content["answer"]

        memory_service.extract_from_chat(
            session_id=session_id,
            query="When should I take the second medicine?",
            answer="Take Amlodipine 5mg once daily in the evening.",
            query_type="medication",
            confidence=0.85,
            turn_number=2,
        )
        entries = memory_service.recall(session_id)
        assert len(entries) == 2
        recalled_answers = [e.content["answer"] for e in entries]
        assert any("Amlodipine" in a for a in recalled_answers)

    def test_scenario2_conversation_history_in_rag(self):
        with patch("app.chat.chat_service.RAGEngine") as mock_rag_cls:
            mock_rag = MagicMock()
            mock_rag.answer.return_value = RAGResponse(
                answer="Take Amlodipine 5mg once daily in the evening.",
                query_type="medication",
            )
            mock_rag_cls.return_value = mock_rag

            memory_service = MemoryService(config=MemoryConfig(
                provider="in_memory", max_memories_per_session=50,
                enable_expiry_policy=False, enable_retention_policy=False,
            ))
            memory_service.extract_from_chat(
                session_id="e2e-s2-context",
                query="What are my meds?",
                answer="Lisinopril 10mg and Amlodipine 5mg.",
                turn_number=1,
            )
            entries = memory_service.recall("e2e-s2-context")
            history_lines = []
            for e in entries[-10:]:
                q = e.content.get("query", "")
                a = e.content.get("answer", "")
                if q and a:
                    history_lines.append(f"User: {q}")
                    history_lines.append(f"Assistant: {a}")
            conversation_history = "\n".join(history_lines)
            assert "Lisinopril" in conversation_history
            assert "Amlodipine" in conversation_history

            service = ChatService()
            response = service.ask(
                ChatRequest(query="When should I take the second med?", session_id="e2e-s2-context"),
                conversation_history=conversation_history,
            )
            assert response.answer
            assert len(mock_rag.answer.call_args_list) >= 1


class TestEndToEndScenario3:
    """Scenario 3: Book follow-up appointment via tool."""

    def test_scenario3_tool_selection_booking(self):
        service = ToolService()
        result = service.run_from_query(
            query="Book my follow-up appointment for next week",
            user_id="u1",
            user_role="patient",
            patient_id="p1",
            doctor_id="d1",
            parameters={"reason": "Follow-up checkup"},
        )
        assert result is not None
        assert isinstance(result.success, bool)

    def test_scenario3_appointment_tool_detection(self):
        service = ToolService()
        result = service.run_from_query(
            query="Schedule a follow-up with Dr. Smith",
            user_id="u1",
            user_role="patient",
            patient_id="p1",
        )
        assert result is not None

    def test_scenario3_then_query_after_booking(self, db_session, client, patient_token):
        service = ToolService()
        result = service.run(
            tool_type="appointment",
            action="list",
            user_id="u1",
            user_role="patient",
            patient_id="p1",
            parameters={"patient_id": "p1"},
        )
        assert result is not None

    def test_scenario3_cancel_then_rebook(self):
        service = ToolService()
        result = service.run_from_query(
            query="Cancel my appointment and book a new one",
            user_id="u1",
            user_role="patient",
            patient_id="p1",
        )
        assert result is not None


class TestEndToEndScenario4:
    """Scenario 4: Summarize latest report with citations."""

    def test_scenario4_report_summary_tool(self):
        service = ToolService()
        result = service.run(
            tool_type="report",
            action="summarize",
            user_id="u1",
            user_role="patient",
            patient_id="p1",
            parameters={"patient_id": "p1", "report_id": "r1"},
        )
        assert result is not None

    def test_scenario4_rag_with_report_context(self):
        with patch("app.chat.chat_service.RAGEngine") as mock_rag_cls:
            from app.rag.models import CitationBlock, CitationEntry
            mock_rag = MagicMock()
            mock_rag.answer.return_value = RAGResponse(
                answer="Your latest report shows a diagnosis of Hypertension. "
                       "Medications include Lisinopril 10mg. [Source: Report #1234]",
                query_type="summary",
                citations=CitationBlock(
                    citations=[CitationEntry(citation_id=1, source="Report #1234", text_snippet="Lisinopril 10mg", document_id="d1", chunk_id="c1")],
                    citation_count=1,
                ),
            )
            mock_rag_cls.return_value = mock_rag
            service = ChatService()
            response = service.ask(
                ChatRequest(query="Summarize my latest report", session_id="e2e-s4"),
            )
            assert response.answer
            assert len(response.answer) > 20

    def test_scenario4_citations_present(self):
        with patch("app.chat.chat_service.RAGEngine") as mock_rag_cls:
            from app.rag.models import CitationBlock, CitationEntry
            mock_rag = MagicMock()
            mock_rag.answer.return_value = RAGResponse(
                answer="Diagnosis: Hypertension. [Source: Report #1234]",
                query_type="summary",
                citations=CitationBlock(
                    citations=[CitationEntry(citation_id=1, source="Report #1234", text_snippet="Hypertension", document_id="d1", chunk_id="c1")],
                    citation_count=1,
                ),
            )
            mock_rag_cls.return_value = mock_rag
            service = ChatService()
            response = service.ask(ChatRequest(query="Summarize", session_id="e2e-s4-cite"))
            assert response.citations is not None


class TestEndToEndScenario5:
    """Scenario 5: Out-of-document question - verify no hallucination."""

    def test_scenario5_no_hallucination_on_unknown(self):
        with patch("app.chat.chat_service.RAGEngine") as mock_rag_cls:
            mock_rag = MagicMock()
            mock_rag.answer.return_value = RAGResponse(
                answer="I don't have enough information in the provided documents to answer this question.",
                query_type="unknown",
            )
            mock_rag_cls.return_value = mock_rag
            service = ChatService()
            response = service.ask(ChatRequest(
                query="What is the patient's family history of cancer?",
                session_id="e2e-s5",
            ))
            assert "don't have enough information" in response.answer.lower() or \
                   "not" in response.answer.lower() or \
                   "cannot" in response.answer.lower()

    def test_scenario5_uncertainty_signal(self):
        with patch("app.chat.chat_service.RAGEngine") as mock_rag_cls:
            mock_rag = MagicMock()
            mock_rag.answer.return_value = RAGResponse(
                answer="The provided documents do not contain information about genetic conditions.",
                query_type="unknown",
            )
            mock_rag_cls.return_value = mock_rag
            service = ChatService()
            response = service.ask(ChatRequest(
                query="Are there any genetic conditions?",
                session_id="e2e-s5-uncertain",
            ))
            uncertainty_phrases = [
                "don't have enough", "not contain", "no information",
                "cannot answer", "not available", "insufficient",
            ]
            has_uncertainty = any(p in response.answer.lower() for p in uncertainty_phrases)
            assert has_uncertainty, f"Expected uncertainty signal, got: {response.answer}"

    def test_scenario5_confidence_low(self):
        with patch("app.chat.chat_service.RAGEngine") as mock_rag_cls:
            mock_rag = MagicMock()
            mock_rag.answer.return_value = RAGResponse(
                answer="I cannot find information about this in the available documents.",
                query_type="unknown",
            )
            mock_rag_cls.return_value = mock_rag
            service = ChatService()
            response = service.ask(ChatRequest(
                query="What is the expected recovery timeline?",
                session_id="e2e-s5-conf",
            ))
            assert response.confidence.overall <= 0.5 or response.confidence.insufficient_evidence
