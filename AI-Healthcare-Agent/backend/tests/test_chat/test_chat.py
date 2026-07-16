from __future__ import annotations

import time
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest

from app.chat.chat_service import ChatService
from app.chat.chat_session import SessionManager
from app.chat.config import ChatConfig
from app.chat.confidence import ConfidenceCalculator, ConfidenceLevel, ConfidenceScore
from app.chat.exceptions import (
    ChatError,
    EmptyQuestionError,
    MaxQuestionsExceededError,
    SessionExpiredError,
    SessionNotFoundError,
)
from app.chat.models import (
    CHAT_SCHEMA_VERSION,
    ChatRequest,
    ChatResponse,
    ChatSession,
    QAPair,
    SuggestedQuestion,
)
from app.chat.question_suggester import QuestionSuggester
from app.chat.response_formatter import ResponseFormatter
from app.rag.models import CitationBlock, CitationEntry, GuardrailResult, RAGResponse


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_mock_rag_response(
    answer: str = "Your medication is lisinopril 10mg daily.",
    query_type: str = "medication",
    num_citations: int = 2,
    guardrail_passed: bool = True,
) -> RAGResponse:
    citations = CitationBlock(
        citations=[
            CitationEntry(
                citation_id=i + 1,
                document_id=f"doc_{i}",
                chunk_id=f"chunk_{i}",
                section="medication",
                text_snippet=f"lisinopril 10mg daily fragment {i}",
                score=0.9 - i * 0.1,
            )
            for i in range(num_citations)
        ],
        citation_count=num_citations,
    )
    return RAGResponse(
        answer=answer,
        citations=citations,
        query="test query",
        query_type=query_type,
        guardrail_result=GuardrailResult(
            passed=guardrail_passed,
            score=1.0 if guardrail_passed else 0.5,
        ),
    )


def make_mock_rag_engine(
    response: Optional[RAGResponse] = None,
    answer: Optional[str] = None,
) -> MagicMock:
    engine = MagicMock()
    if answer is not None:
        resp = make_mock_rag_response(answer=answer)
        engine.answer.return_value = resp
    else:
        engine.answer.return_value = response or make_mock_rag_response()
    return engine


# ─────────────────────────────────────────────
# Tests: Config
# ─────────────────────────────────────────────

class TestChatConfig:
    def test_defaults(self):
        config = ChatConfig()
        assert config.session_timeout_minutes == 30
        assert config.max_questions_per_session == 50
        assert config.max_suggested_questions == 5

    def test_custom_values(self):
        config = ChatConfig(session_timeout_minutes=60, max_suggested_questions=3)
        assert config.session_timeout_minutes == 60
        assert config.max_suggested_questions == 3


# ─────────────────────────────────────────────
# Tests: Exceptions
# ─────────────────────────────────────────────

class TestChatExceptions:
    def test_hierarchy(self):
        assert issubclass(ChatError, Exception)
        assert issubclass(SessionNotFoundError, ChatError)
        assert issubclass(SessionExpiredError, ChatError)
        assert issubclass(MaxQuestionsExceededError, ChatError)
        assert issubclass(EmptyQuestionError, ChatError)

    def test_exception_messages(self):
        exc = SessionNotFoundError("test error")
        assert str(exc) == "test error"


# ─────────────────────────────────────────────
# Tests: Models
# ─────────────────────────────────────────────

class TestChatModels:
    def test_chat_response_defaults(self):
        resp = ChatResponse(answer="test")
        assert resp.answer == "test"
        assert resp.schema_version == CHAT_SCHEMA_VERSION

    def test_chat_session_defaults(self):
        session = ChatSession(session_id="test")
        assert session.session_id == "test"
        assert session.questions == []

    def test_confidence_score_defaults(self):
        cs = ConfidenceScore()
        assert cs.overall == 0.0
        assert cs.level == ConfidenceLevel.insufficient_evidence

    def test_suggested_question(self):
        sq = SuggestedQuestion(question="Test?", category="general", priority=1)
        assert sq.question == "Test?"

    def test_qa_pair_defaults(self):
        qa = QAPair(question="q", answer="a")
        assert qa.question == "q"
        assert qa.answer == "a"

    def test_chat_request_defaults(self):
        req = ChatRequest(query="What is my diagnosis?")
        assert req.query == "What is my diagnosis?"
        assert req.enable_citations is True


# ─────────────────────────────────────────────
# Tests: Session Manager
# ─────────────────────────────────────────────

class TestSessionManager:
    def test_create_session(self):
        mgr = SessionManager()
        session = mgr.create_session(session_id="s1", document_type="lab_report")
        assert session.session_id == "s1"
        assert session.document_type == "lab_report"

    def test_get_session(self):
        mgr = SessionManager()
        mgr.create_session(session_id="s1")
        session = mgr.get_session("s1")
        assert session.session_id == "s1"

    def test_get_session_not_found(self):
        mgr = SessionManager()
        with pytest.raises(SessionNotFoundError):
            mgr.get_session("nonexistent")

    def test_get_session_expired(self):
        mgr = SessionManager(config=ChatConfig(session_timeout_minutes=0))
        mgr.create_session(session_id="s1")
        time.sleep(0.01)
        with pytest.raises(SessionExpiredError):
            mgr.get_session("s1")

    def test_add_qa_pair(self):
        mgr = SessionManager()
        mgr.create_session(session_id="s1")
        qa = QAPair(question="q", answer="a")
        mgr.add_qa_pair("s1", qa)
        assert len(mgr.get_session("s1").questions) == 1

    def test_max_questions_exceeded(self):
        mgr = SessionManager(config=ChatConfig(max_questions_per_session=1))
        mgr.create_session(session_id="s1")
        mgr.add_qa_pair("s1", QAPair(question="q1", answer="a1"))
        with pytest.raises(MaxQuestionsExceededError):
            mgr.add_qa_pair("s1", QAPair(question="q2", answer="a2"))

    def test_get_recent_qa(self):
        mgr = SessionManager()
        mgr.create_session(session_id="s1")
        for i in range(5):
            mgr.add_qa_pair("s1", QAPair(question=f"q{i}", answer=f"a{i}"))
        recent = mgr.get_recent_qa("s1", count=3)
        assert len(recent) == 3

    def test_delete_session(self):
        mgr = SessionManager()
        mgr.create_session(session_id="s1")
        mgr.delete_session("s1")
        assert mgr.session_count() == 0

    def test_cleanup_expired(self):
        mgr = SessionManager(config=ChatConfig(session_timeout_minutes=0))
        mgr.create_session(session_id="s1")
        mgr.create_session(session_id="s2")
        time.sleep(0.01)
        cleaned = mgr.cleanup_expired()
        assert cleaned == 2

    def test_is_follow_up(self):
        mgr = SessionManager()
        mgr.create_session(session_id="s1")
        assert mgr.is_follow_up_question("s1") is False
        mgr.add_qa_pair("s1", QAPair(question="q", answer="a"))
        assert mgr.is_follow_up_question("s1") is True

    def test_update_document(self):
        mgr = SessionManager()
        mgr.create_session(session_id="s1")
        mgr.update_document(
            session_id="s1",
            document_id="doc_new",
            document_sections=["diagnosis", "medication"],
        )
        session = mgr.get_session("s1")
        assert session.document_id == "doc_new"
        assert session.document_has_diagnosis is True
        assert session.document_has_medication is True

    def test_document_flags(self):
        mgr = SessionManager()
        mgr.create_session(
            session_id="s1",
            document_sections=["diagnosis", "medication", "lab_results", "plan"],
        )
        session = mgr.get_session("s1")
        assert session.document_has_diagnosis is True
        assert session.document_has_medication is True
        assert session.document_has_lab_results is True
        assert session.document_has_follow_up is True


# ─────────────────────────────────────────────
# Tests: Confidence Calculator
# ─────────────────────────────────────────────

class TestConfidenceCalculator:
    def test_high_confidence(self):
        calc = ConfidenceCalculator()
        result = calc.calculate(
            retrieval_scores=[0.9, 0.8, 0.7],
            num_chunks=3,
            num_citations=3,
            guardrail_passed=True,
            answer_text="Your medication is lisinopril.",
            has_sufficient_context=True,
        )
        assert result.level == ConfidenceLevel.high
        assert result.overall >= 0.7

    def test_medium_confidence(self):
        calc = ConfidenceCalculator()
        result = calc.calculate(
            retrieval_scores=[0.4],
            num_chunks=1,
            num_citations=0,
            guardrail_passed=True,
            answer_text="Some information.",
            has_sufficient_context=True,
        )
        assert result.level == ConfidenceLevel.medium
        assert result.overall < 0.7

    def test_insufficient_evidence_no_context(self):
        calc = ConfidenceCalculator()
        result = calc.calculate(
            retrieval_scores=[],
            num_chunks=0,
            num_citations=0,
            guardrail_passed=False,
            answer_text="",
            has_sufficient_context=False,
        )
        assert result.insufficient_evidence is True
        assert result.level == ConfidenceLevel.insufficient_evidence

    def test_insufficient_evidence_unknown_phrase(self):
        calc = ConfidenceCalculator()
        result = calc.calculate(
            retrieval_scores=[0.3],
            num_chunks=1,
            num_citations=0,
            guardrail_passed=True,
            answer_text="I don't have enough information to answer.",
            has_sufficient_context=True,
        )
        assert result.insufficient_evidence is True

    def test_guardrail_failure_lowers_confidence(self):
        calc = ConfidenceCalculator()
        result = calc.calculate(
            retrieval_scores=[0.9, 0.8],
            num_chunks=2,
            num_citations=2,
            guardrail_passed=True,
            answer_text="Good answer.",
            has_sufficient_context=True,
        )
        high_score = result.overall

        result2 = calc.calculate(
            retrieval_scores=[0.9, 0.8],
            num_chunks=2,
            num_citations=2,
            guardrail_passed=False,
            guardrail_failures=["Unsupported claims detected"],
            answer_text="Good answer.",
            has_sufficient_context=True,
        )
        assert result2.overall < high_score

    def test_low_confidence(self):
        calc = ConfidenceCalculator(min_chunks=5)
        result = calc.calculate(
            retrieval_scores=[0.1],
            num_chunks=1,
            num_citations=0,
            guardrail_passed=True,
            answer_text="Some info.",
            has_sufficient_context=True,
        )
        assert result.level == ConfidenceLevel.low


# ─────────────────────────────────────────────
# Tests: Question Suggester
# ─────────────────────────────────────────────

class TestQuestionSuggester:
    def test_suggest_diagnosis_questions(self):
        suggester = QuestionSuggester()
        questions = suggester.suggest(
            document_has_diagnosis=True,
        )
        assert len(questions) > 0
        assert any("diagnosis" in q.question.lower() for q in questions)

    def test_suggest_medication_questions(self):
        suggester = QuestionSuggester()
        questions = suggester.suggest(
            document_has_medication=True,
        )
        assert any("medicine" in q.question.lower() for q in questions)

    def test_suggest_lab_result_questions(self):
        suggester = QuestionSuggester()
        questions = suggester.suggest(
            document_has_lab_results=True,
        )
        assert any("lab" in q.question.lower() for q in questions)

    def test_suggest_follow_up_questions(self):
        suggester = QuestionSuggester()
        questions = suggester.suggest(
            document_has_follow_up=True,
        )
        assert any("follow" in q.question.lower() for q in questions)

    def test_universal_questions_when_no_sections(self):
        suggester = QuestionSuggester()
        questions = suggester.suggest()
        assert len(questions) > 0
        assert any("health" in q.question.lower() for q in questions)

    def test_excludes_recent_questions(self):
        suggester = QuestionSuggester()
        questions = suggester.suggest(
            document_has_diagnosis=True,
            recent_questions=["Explain my diagnosis."],
        )
        assert not any(
            "explain my diagnosis" in q.question.lower() for q in questions
        )

    def test_suggest_from_sections(self):
        suggester = QuestionSuggester()
        questions = suggester.suggest_from_sections(
            ["diagnosis", "medication"]
        )
        assert len(questions) > 0

    def test_max_suggestions(self):
        suggester = QuestionSuggester(max_suggestions=2)
        questions = suggester.suggest(
            document_has_diagnosis=True,
            document_has_medication=True,
            document_has_lab_results=True,
        )
        assert len(questions) <= 2

    def test_priority_ordering(self):
        suggester = QuestionSuggester()
        questions = suggester.suggest(
            document_has_diagnosis=True,
        )
        if len(questions) >= 2:
            assert questions[0].priority <= questions[1].priority


# ─────────────────────────────────────────────
# Tests: Response Formatter
# ─────────────────────────────────────────────

class TestResponseFormatter:
    def test_format_high_confidence_answer(self):
        fmt = ResponseFormatter()
        confidence = ConfidenceScore(overall=0.85, level=ConfidenceLevel.high)
        result = fmt.format_answer(
            answer="Your diagnosis is hypertension.",
            confidence=confidence,
        )
        assert "Your diagnosis is hypertension" in result["answer"]

    def test_format_low_confidence_answer(self):
        fmt = ResponseFormatter()
        confidence = ConfidenceScore(overall=0.3, level=ConfidenceLevel.low)
        result = fmt.format_answer(
            answer="Some information found.",
            confidence=confidence,
        )
        assert "Based on the available information" in result["answer"]

    def test_format_unknown_answer(self):
        fmt = ResponseFormatter()
        confidence = ConfidenceScore(
            overall=0.1, level=ConfidenceLevel.insufficient_evidence,
            insufficient_evidence=True,
        )
        result = fmt.format_answer(
            answer="I don't have enough information.",
            confidence=confidence,
        )
        assert "I don't have enough information to answer" in result["answer"]

    def test_format_citations_deduplication(self):
        fmt = ResponseFormatter()
        citations = [
            {"chunk_id": "c1", "citation_id": 1, "document_id": "d1", "text_snippet": "text1"},
            {"chunk_id": "c1", "citation_id": 1, "document_id": "d1", "text_snippet": "text1"},
            {"chunk_id": "c2", "citation_id": 2, "document_id": "d2", "text_snippet": "text2"},
        ]
        result = fmt._format_citations(citations, "answer")
        assert len(result) == 2

    def test_report_summary(self):
        fmt = ResponseFormatter()
        confidence = ConfidenceScore(overall=0.7, level=ConfidenceLevel.high)
        summary = fmt.format_report_summary(
            answer="Patient has hypertension.",
            sections=["diagnosis", "medication"],
            confidence=confidence,
        )
        assert "Medical Report Summary" in summary
        assert "Patient has hypertension" in summary


# ─────────────────────────────────────────────
# Tests: Chat Service
# ─────────────────────────────────────────────

class TestChatService:
    def test_ask_with_mock_rag(self):
        mock_rag = make_mock_rag_engine()
        service = ChatService(rag_engine=mock_rag)
        request = ChatRequest(query="What medication?")
        response = service.ask(request)
        assert response.answer is not None
        assert len(response.session_id) > 0
        assert response.processing_time_ms >= 0

    def test_ask_empty_query_raises(self):
        service = ChatService(rag_engine=MagicMock())
        with pytest.raises(EmptyQuestionError):
            service.ask(ChatRequest(query=""))
        with pytest.raises(EmptyQuestionError):
            service.ask(ChatRequest(query="   "))

    def test_ask_session_id_reuse(self):
        mock_rag = make_mock_rag_engine()
        service = ChatService(rag_engine=mock_rag)
        resp1 = service.ask(ChatRequest(query="First question?"))
        resp2 = service.ask(ChatRequest(
            query="Follow up?",
            session_id=resp1.session_id,
        ))
        assert resp2.session_id == resp1.session_id

    def test_ask_with_citations(self):
        mock_rag = make_mock_rag_engine()
        service = ChatService(rag_engine=mock_rag)
        response = service.ask(ChatRequest(query="What medication?"))
        assert isinstance(response.citations, list)

    def test_ask_with_suggestions(self):
        mock_rag = make_mock_rag_engine()
        service = ChatService(rag_engine=mock_rag)
        request = ChatRequest(
            query="What medication?",
            document_sections=["diagnosis", "medication"],
        )
        response = service.ask(request)
        assert len(response.suggested_questions) >= 0

    def test_get_session_questions(self):
        mock_rag = make_mock_rag_engine()
        service = ChatService(rag_engine=mock_rag)
        resp = service.ask(ChatRequest(query="First question?"))
        questions = service.get_session_questions(resp.session_id)
        assert len(questions) == 1
        assert questions[0].question == "First question?"

    def test_create_session(self):
        service = ChatService(rag_engine=MagicMock())
        sid = service.create_session(
            document_type="lab_report",
            document_sections=["diagnosis"],
        )
        assert len(sid) > 0
        assert service.get_session_count() == 1

    def test_delete_session(self):
        service = ChatService(rag_engine=MagicMock())
        sid = service.create_session()
        service.delete_session(sid)
        assert service.get_session_count() == 0

    def test_update_session_document(self):
        service = ChatService(rag_engine=MagicMock())
        sid = service.create_session()
        service.update_session_document(
            session_id=sid,
            document_id="doc_1",
            document_sections=["medication"],
        )
        questions = service.get_session_questions(sid, 5)
        assert len(questions) == 0

    def test_cleanup_expired_sessions(self):
        config = ChatConfig(session_timeout_minutes=0)
        service = ChatService(rag_engine=MagicMock(), config=config)
        service.create_session()
        time.sleep(0.01)
        cleaned = service.cleanup_expired_sessions()
        assert cleaned >= 1

    def test_rag_engine_failure_raises(self):
        mock_rag = MagicMock()
        mock_rag.answer.side_effect = RuntimeError("Engine failure")
        service = ChatService(rag_engine=mock_rag)
        with pytest.raises(ChatError):
            service.ask(ChatRequest(query="What?"))


# ─────────────────────────────────────────────
# Tests: Multi-turn Conversation
# ─────────────────────────────────────────────

class TestMultiTurnConversation:
    def test_two_turns_same_session(self):
        mock_rag = make_mock_rag_engine(
            answer="Your medication is lisinopril."
        )
        service = ChatService(rag_engine=mock_rag)

        resp1 = service.ask(ChatRequest(query="What medication?"))
        assert resp1.session_id

        mock_rag.answer.return_value = make_mock_rag_response(
            answer="Take 10mg daily."
        )
        resp2 = service.ask(ChatRequest(
            query="What dosage?",
            session_id=resp1.session_id,
        ))
        assert resp2.session_id == resp1.session_id
        assert resp2.is_follow_up is True

        questions = service.get_session_questions(resp1.session_id, 5)
        assert len(questions) == 2

    def test_three_turns(self):
        mock_rag = make_mock_rag_engine()
        service = ChatService(rag_engine=mock_rag)

        r1 = service.ask(ChatRequest(query="What is my diagnosis?"))
        r2 = service.ask(ChatRequest(
            query="What medication?", session_id=r1.session_id,
        ))
        r3 = service.ask(ChatRequest(
            query="What dosage?", session_id=r1.session_id,
        ))
        assert r3.session_id == r1.session_id
        assert r3.session_id == r2.session_id
        questions = service.get_session_questions(r1.session_id, 5)
        assert len(questions) == 3


# ─────────────────────────────────────────────
# Tests: Edge Cases
# ─────────────────────────────────────────────

class TestChatEdgeCases:
    def test_confidence_with_no_citations(self):
        calc = ConfidenceCalculator()
        result = calc.calculate(
            retrieval_scores=[],
            num_chunks=0,
            num_citations=0,
            guardrail_passed=True,
            answer_text="Some answer.",
            has_sufficient_context=False,
        )
        assert result.insufficient_evidence is True

    def test_formatter_empty_citations(self):
        fmt = ResponseFormatter()
        confidence = ConfidenceScore(overall=0.9, level=ConfidenceLevel.high)
        result = fmt.format_answer(
            answer="Test",
            confidence=confidence,
            citations=[],
        )
        assert result["citations"] == []

    def test_suggester_empty_sections(self):
        suggester = QuestionSuggester()
        questions = suggester.suggest_from_sections([])
        assert len(questions) > 0

    def test_session_manager_count(self):
        mgr = SessionManager()
        assert mgr.session_count() == 0
        mgr.create_session(session_id="s1")
        assert mgr.session_count() == 1

    def test_session_manager_unknown_session_not_follow_up(self):
        mgr = SessionManager()
        assert mgr.is_follow_up_question("nonexistent") is False


# ─────────────────────────────────────────────
# Tests: Module Exports
# ─────────────────────────────────────────────

class TestChatExports:
    def test_module_imports(self):
        from app.chat import ChatService, ChatConfig, ChatRequest, ChatResponse
        assert ChatService is not None
        assert ChatConfig is not None
        assert ChatRequest is not None
        assert ChatResponse is not None

    def test_schema_version(self):
        assert CHAT_SCHEMA_VERSION == "1.0.0"
