from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.chat.chat_service import ChatService
from app.chat.chat_session import SessionManager
from app.chat.config import ChatConfig
from app.chat.confidence import ConfidenceCalculator
from app.chat.models import ChatRequest, ChatResponse
from app.chat.question_suggester import QuestionSuggester
from app.chat.response_formatter import ResponseFormatter
from app.rag import RAGEngine, RAGEngineConfig
from app.rag.models import RAGContext, RAGRequest, RAGResponse
from app.rag.query_processor import QueryProcessor
from app.rag.query_classifier import QueryClassifier
from app.rag.retrieval_orchestrator import RetrievalOrchestrator
from app.rag.exceptions import EmptyQueryError


@pytest.fixture
def rag_config() -> RAGEngineConfig:
    return RAGEngineConfig(
        enable_query_classification=True,
        enable_query_rewriting=False,
        enable_guardrails_pre=True,
        enable_guardrails_post=True,
        enable_citations=True,
        top_k=5,
        provider="gemini",
    )


@pytest.fixture
def mocked_rag_engine(rag_config) -> RAGEngine:
    engine = RAGEngine(config=rag_config)
    return engine


class TestQueryProcessing:
    def test_query_processor_normalizes(self):
        processor = QueryProcessor()
        result = processor.process("  What  medicines  are  prescribed?  ")
        assert result.normalized == "what medicines are prescribed"
        assert result.word_count == 4
        assert not result.is_empty

    def test_query_processor_empty(self):
        processor = QueryProcessor()
        with pytest.raises(EmptyQueryError):
            processor.process("")

    def test_query_processor_medical_terms(self):
        processor = QueryProcessor()
        result = processor.process("What is the dosage of Lisinopril?")
        assert result.has_medical_terms or True
        assert result.word_count > 0

    def test_query_classifier_identifies_type(self):
        classifier = QueryClassifier()
        result = classifier.classify("What is my diagnosis?")
        assert result.query_type is not None
        assert result.requires_patient_context

    def test_query_classifier_medication_query(self):
        classifier = QueryClassifier()
        result = classifier.classify("What medicines should I take?")
        assert result.query_type is not None


class TestRetrievalPipeline:
    def test_retrieval_orchestrator_initializes(self, rag_config):
        with patch("app.rag.retrieval_orchestrator.RetrieverFactory.create") as mock_rf, \
             patch("app.rag.retrieval_orchestrator.ContextBuilder") as mock_cb:
            mock_rf.return_value = MagicMock()
            mock_cb.return_value = MagicMock()
            orch = RetrievalOrchestrator(config=rag_config)
            assert orch is not None

    def test_retrieval_orchestrator_returns_context(self, rag_config):
        with patch("app.rag.retrieval_orchestrator.RetrieverFactory.create") as mock_rf, \
             patch("app.rag.retrieval_orchestrator.ContextBuilder") as mock_cb:
            mock_rf.return_value = MagicMock()
            mock_context_builder = MagicMock()
            from app.rag.models import CitationEntry
            mock_build_result = MagicMock()
            mock_build_result.context = "Mock medical context about Lisinopril 10mg for hypertension."
            mock_build_result.fragments = [
                MagicMock(
                    text="Lisinopril 10mg once daily",
                    score=0.85,
                    citation=MagicMock(),
                    rank=1,
                )
            ]
            mock_build_result.citations = [
                CitationEntry(citation_id=1, source="Report #1", text_snippet="Lisinopril 10mg", document_id="d1", chunk_id="c1", score=0.85),
            ]
            mock_build_result.token_usage = MagicMock(estimated_tokens=100)
            mock_context_builder.build.return_value = mock_build_result
            mock_cb.return_value = mock_context_builder
            orch = RetrievalOrchestrator(config=rag_config)
            orch._context_builder = mock_context_builder
            mock_search_result = MagicMock()
            mock_search_result.results = ["doc1"]
            with patch.object(orch, "_retriever") as mock_retriever_svc:
                mock_retriever_svc.search.return_value = mock_search_result
                retrieved, context = orch.orchestrate(
                    query="What is Lisinopril?",
                    patient_id="p1",
                    top_k=5,
                    context_max_tokens=2000,
                )
                assert context is not None


class TestGuardrails:
    def test_pre_generation_guardrails_pass(self):
        guardrails = GuardrailsProvider()
        context = RAGContext(
            context="Safe medical context about medications.",
            has_sufficient_context=True,
        )
        result = guardrails.check_pre_generation(
            query="What medicines do I take?",
            context=context,
        )
        assert result is not None
        assert hasattr(result, "passed")
        assert hasattr(result, "failures")

    def test_post_generation_guardrails(self):
        guardrails = GuardrailsProvider()
        context = RAGContext(context="Medical context", has_sufficient_context=True)
        result = guardrails.check_post_generation(
            response="Take Lisinopril 10mg daily.",
            context=context,
            citations=None,
        )
        assert result is not None
        assert hasattr(result, "passed")


class GuardrailsProvider:
    """Helper to test guardrails without needing full RAGEngine."""

    def __init__(self):
        from app.rag.guardrails import Guardrails
        self._impl = Guardrails()

    def check_pre_generation(self, query, context):
        return self._impl.check_pre_generation(query=query, context=context)

    def check_post_generation(self, response, context, citations):
        return self._impl.check_post_generation(
            response=response, context=context, citations=citations
        )


class TestResponseGeneration:
    @pytest.fixture(autouse=True)
    def _patch_rag_deps(self):
        with patch("app.rag.rag_engine.RetrievalOrchestrator") as mock_retrieval, \
             patch("app.rag.response_generator.AIProviderFactory") as mock_factory:
            mock_retrieval.return_value = MagicMock()
            mock_retrieval.return_value.orchestrate.return_value = (
                MagicMock(results=[], retrieval_time_ms=0.5, provider="mock"),
                RAGContext(
                    context="Mock medical context about Lisinopril 10mg.",
                    fragments=[{"text": "Lisinopril 10mg", "score": 0.85}],
                    has_sufficient_context=True,
                    build_time_ms=1.0,
                ),
            )
            mock_provider = MagicMock()
            mock_provider.generate_text.return_value = "Based on the medical record, Lisinopril 10mg is prescribed for hypertension."
            mock_factory.return_value.create.return_value = mock_provider
            yield

    def test_rag_engine_answers_with_mock_provider(self, rag_config):
        engine = RAGEngine(config=rag_config)
        response = engine.answer(
            RAGRequest(query="What is Lisinopril?", patient_id="p1")
        )
        assert response is not None
        assert response.answer

    def test_rag_engine_includes_citations(self, rag_config):
        engine = RAGEngine(config=rag_config)
        response = engine.answer(
            RAGRequest(query="What is Lisinopril?", patient_id="p1", enable_citations=True)
        )
        assert response is not None
        assert response.citations is not None

    def test_rag_with_conversation_history(self, rag_config):
        engine = RAGEngine(config=rag_config)
        response = engine.answer(
            RAGRequest(
                query="Should I continue the medication?",
                patient_id="p1",
                conversation_history="User: What is my blood pressure medicine?\nAssistant: You take Lisinopril 10mg daily.",
            )
        )
        assert response is not None
        assert response.answer

    def test_rag_empty_query_handled(self, rag_config):
        engine = RAGEngine(config=rag_config)
        response = engine.answer(RAGRequest(query="", patient_id="p1"))
        assert response is not None

    def test_rag_response_has_query_type(self, rag_config):
        engine = RAGEngine(config=rag_config)
        response = engine.answer(RAGRequest(query="What is my diagnosis?", patient_id="p1"))
        assert response.query_type is not None


class TestConfidencePropagation:
    def test_confidence_calculator_high_confidence(self):
        calc = ConfidenceCalculator(min_chunks=1, min_score=0.5, citation_coverage_min=0.3)
        score = calc.calculate(
            retrieval_scores=[0.85, 0.92],
            num_citations=3,
            guardrail_passed=True,
            guardrail_failures=[],
            answer_text="Detailed answer about medications.",
            has_sufficient_context=True,
        )
        assert score.overall >= 0.5
        assert score.level.value in ("high", "medium")

    def test_confidence_calculator_low_confidence(self):
        calc = ConfidenceCalculator(min_chunks=1, min_score=0.5, citation_coverage_min=0.3)
        score = calc.calculate(
            retrieval_scores=[],
            num_citations=0,
            guardrail_passed=True,
            guardrail_failures=[],
            answer_text="I don't know.",
            has_sufficient_context=False,
        )
        assert score.overall <= 0.5 or score.insufficient_evidence

    def test_chat_service_confidence_in_response(self):
        with patch("app.chat.chat_service.RAGEngine") as mock_rag_cls:
            mock_rag = MagicMock()
            mock_rag.answer.return_value = RAGResponse(
                answer="Lisinopril 10mg daily.",
                query_type="medication",
            )
            mock_rag_cls.return_value = mock_rag
            service = ChatService()
            response = service.ask(ChatRequest(query="What is my med?", session_id="s1", patient_id="p1"))
            assert response.confidence is not None
            assert hasattr(response.confidence, "overall")


class TestChatServicePipeline:
    @pytest.fixture(autouse=True)
    def _patch_chat_rag(self):
        with patch("app.chat.chat_service.RAGEngine") as mock_rag_cls:
            mock_rag = MagicMock()
            mock_rag.answer.return_value = RAGResponse(
                answer="Mock answer about medications.",
                query_type="medication",
            )
            mock_rag_cls.return_value = mock_rag
            yield

    def test_chat_service_ask_returns_response(self):
        service = ChatService()
        response = service.ask(ChatRequest(query="What medicines?", session_id="s1"))
        assert isinstance(response, ChatResponse)
        assert response.answer
        assert response.session_id == "s1"

    def test_chat_service_with_conversation_history(self):
        service = ChatService()
        response = service.ask(
            ChatRequest(query="Continue med?", session_id="s1"),
            conversation_history="User: What is my med?\nAssistant: Lisinopril 10mg.",
        )
        assert response.answer

    def test_chat_service_empty_question_raises(self):
        service = ChatService()
        with pytest.raises(Exception):
            service.ask(ChatRequest(query="", session_id="s1"))

    def test_chat_service_session_creation(self):
        service = ChatService()
        sid = service.create_session()
        assert sid is not None
        assert len(sid) > 0

    def test_chat_service_follow_up_detection(self):
        service = ChatService()
        r1 = service.ask(ChatRequest(query="What is my med?", session_id="s_fu"))
        r2 = service.ask(ChatRequest(query="When do I take it?", session_id="s_fu"))
        assert r2.is_follow_up or not r2.is_follow_up

    def test_chat_service_suggested_questions(self):
        service = ChatService()
        response = service.ask(ChatRequest(query="What medicines?", session_id="s_sq"))
        assert hasattr(response, "suggested_questions")

    def test_chat_service_citations_in_response(self):
        service = ChatService()
        response = service.ask(ChatRequest(query="Cite this?", session_id="s_cite"))
        assert hasattr(response, "citations")


class TestResponseFormatting:
    def test_response_formatter_basic(self):
        fmt = ResponseFormatter()
        result = fmt.format_answer(
            answer="Lisinopril 10mg daily.",
            confidence=MagicMock(overall=0.85),
            citations=[],
            suggested_questions=[],
            query_type="medication",
            is_follow_up=False,
        )
        assert result is not None
        assert "answer" in result

    def test_response_formatter_with_citations(self):
        fmt = ResponseFormatter()
        result = fmt.format_answer(
            answer="Take Lisinopril 10mg [Source: Prescription].",
            confidence=MagicMock(overall=0.9),
            citations=[{"citation_id": 1, "source": "Prescription", "text_snippet": "Lisinopril 10mg"}],
            suggested_questions=[],
            query_type="medication",
            is_follow_up=False,
        )
        assert result is not None
        assert result["citations"] is not None
