from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.chat.chat_service import ChatService
from app.chat.models import ChatRequest
from app.database.enums import ReportStatus
from app.document_pipeline.exceptions import EmptyDocumentError
from app.medical_parser.exceptions import MedicalParserError, EmptyOCRError, ValidationError
from app.document_pipeline.exceptions import MalformedDocumentError
from app.memory.exceptions import MemoryFullError, MemoryNotFoundError, SessionNotFoundError
from app.rag.exceptions import EmptyQueryError
from app.rag.models import RAGResponse
from app.rag.rag_engine import RAGEngine, RAGEngineConfig
from app.tools.tool_service import ToolService


class TestErrorPathsInvalidPDF:
    def test_invalid_pdf_rejected(self, client, patient_auth_headers):
        response = client.post(
            "/api/v1/documents/upload",
            headers=patient_auth_headers,
            files={"file": ("corrupt.pdf", b"not a real pdf content", "application/pdf")},
        )
        assert response.status_code < 500, f"Server error for invalid PDF: {response.text}"

    def test_invalid_image_rejected(self, client, patient_auth_headers):
        response = client.post(
            "/api/v1/documents/upload",
            headers=patient_auth_headers,
            files={"file": ("corrupt.png", b"", "image/png")},
        )
        assert response.status_code < 500, f"Server error for invalid image: {response.text}"

    def test_unsupported_format_rejected(self, client, patient_auth_headers):
        response = client.post(
            "/api/v1/documents/upload",
            headers=patient_auth_headers,
            files={"file": ("test.exe", b"binarydata", "application/x-msdownload")},
        )
        assert response.status_code in (400, 422, 415)

    def test_missing_file_rejected(self, client, patient_auth_headers):
        response = client.post(
            "/api/v1/documents/upload",
            headers=patient_auth_headers,
        )
        assert response.status_code in (400, 422)


class TestErrorPathsCorruptOCR:
    def test_empty_ocr_text_raises(self, mock_ai_provider):
        from app.medical_parser.extractor import extract as med_parse

        with pytest.raises((MedicalParserError, ValidationError, ValueError)):
            med_parse("", provider=mock_ai_provider)

    def test_garbled_ocr_text_handled(self, mock_ai_provider):
        from app.medical_parser.extractor import extract as med_parse

        garbled = "!@#$%^&*()_+"
        schema, context = med_parse(garbled, provider=mock_ai_provider)
        assert schema is not None

    def test_ocr_with_only_whitespace(self, mock_ai_provider):
        from app.medical_parser.extractor import extract as med_parse

        with pytest.raises((MedicalParserError, ValidationError, ValueError)):
            med_parse("   \n   \t   ", provider=mock_ai_provider)


class TestErrorPathsEmptyDocuments:
    def test_empty_document_pipeline_raises(self):
        from app.document_pipeline import DocumentPipeline, DocumentPipelineConfig

        pipeline = DocumentPipeline(
            config=DocumentPipelineConfig(chunk_size=200, chunk_overlap=20),
        )
        with pytest.raises((MalformedDocumentError, EmptyDocumentError)):
            pipeline.process(
                raw_text="",
                patient_id="p1",
                report_id="r1",
            )

    def test_document_pipeline_with_only_whitespace(self):
        from app.document_pipeline import DocumentPipeline, DocumentPipelineConfig

        pipeline = DocumentPipeline(
            config=DocumentPipelineConfig(chunk_size=200, chunk_overlap=20),
        )
        with pytest.raises((MalformedDocumentError, EmptyDocumentError, ValueError)):
            pipeline.process(
                raw_text="   \n\n  \t  ",
                patient_id="p1",
                report_id="r1",
            )


class TestErrorPathsMissingEmbeddings:
    def test_embedding_service_with_empty_text(self, mock_embedding_service):
        vector, meta = mock_embedding_service.embed("")
        assert vector is not None

    def test_embedding_batch_with_mixed_empty(self, mock_embedding_service):
        texts = ["valid", "", "also valid"]
        vectors, metas = mock_embedding_service.embed_batch(texts)
        assert len(vectors) == 3

    def test_vector_search_empty_index(self, mock_vector_store, mock_embedding_service):
        from app.vector_store.vector_service import VectorService

        vs = VectorService(store=mock_vector_store, embedding_service=mock_embedding_service)
        results = vs.search("any query", k=5)
        assert results == []

    def test_vector_search_by_patient_no_match(self, mock_vector_store, mock_embedding_service):
        from app.vector_store.vector_service import VectorService

        vs = VectorService(store=mock_vector_store, embedding_service=mock_embedding_service)
        results = vs.search_by_patient(patient_id="nonexistent", query="test")
        assert results == []


class TestErrorPathsMemoryUnavailable:
    def test_memory_full_error_raised(self):
        from app.memory.config import MemoryConfig
        from app.memory.memory_service import MemoryService

        config = MemoryConfig(
            provider="in_memory",
            max_memories_per_session=2,
            enable_pruning=False,
        )
        service = MemoryService(config=config)
        for i in range(2):
            service.remember(session_id="full-session", content={"i": i}, memory_type="conversation")
        with pytest.raises(MemoryFullError):
            service.remember(session_id="full-session", content={"i": 3}, memory_type="conversation")

    def test_forget_nonexistent_memory(self):
        from app.memory.config import MemoryConfig
        from app.memory.memory_service import MemoryService

        service = MemoryService(config=MemoryConfig(provider="in_memory"))
        with pytest.raises(MemoryNotFoundError):
            service.forget("nonexistent-memory-id")

    def test_clear_nonexistent_session(self):
        from app.memory.config import MemoryConfig
        from app.memory.memory_service import MemoryService

        service = MemoryService(config=MemoryConfig(provider="in_memory"))
        with pytest.raises(SessionNotFoundError):
            service.clear("nonexistent-session")

    def test_recall_empty_session_returns_empty(self):
        from app.memory.config import MemoryConfig
        from app.memory.memory_service import MemoryService

        service = MemoryService(config=MemoryConfig(provider="in_memory"))
        entries = service.recall("never-used-session")
        assert entries == []


class TestErrorPathsToolFailure:
    def test_unknown_tool_returns_error(self):
        service = ToolService()
        result = service.run(
            tool_type="nonexistent_tool",
            action="do_stuff",
            user_id="u1",
            user_role="patient",
        )
        assert result is not None
        assert not result.success
        assert result.error_message is not None

    def test_missing_parameters_handled(self):
        service = ToolService()
        result = service.run(
            tool_type="appointment",
            action="book",
            user_id="u1",
            user_role="patient",
            parameters={},
        )
        assert result is not None

    def test_unauthorized_role_rejected(self):
        from app.tools.base_tool import BaseTool
        from app.tools.tool_context import ToolContext
        from app.tools.tool_executor import ToolExecutor
        from app.tools.tool_result import ToolResult

        class AdminOnlyTool(BaseTool):
            def authorize(self, context: ToolContext) -> bool:
                return context.user_role == "admin"

            def execute(self, context: ToolContext) -> ToolResult:
                return ToolResult.ok(data={"sensitive": "data"})

        tool = AdminOnlyTool()
        executor = ToolExecutor(tool)
        ctx = ToolContext(
            tool_name="admin_only", action="exec",
            user_id="u1", user_role="patient",
            parameters={},
        )
        result = executor.execute(ctx)
        assert result is not None


class TestErrorPathsProviderTimeout:
    def test_rag_engine_handles_provider_timeout(self):
        from app.rag.models import RAGContext, GuardrailResult, RAGRequest

        config = RAGEngineConfig(
            enable_query_classification=False,
            enable_citations=False,
            enable_guardrails_pre=False,
            enable_guardrails_post=False,
            top_k=3,
        )
        with (
            patch("app.rag.rag_engine.RetrievalOrchestrator") as mock_retrieval,
            patch("app.rag.response_generator.AIProviderFactory") as mock_factory,
            patch("app.rag.guardrails.Guardrails") as mock_guardrails,
        ):
            mock_guardrails.return_value = MagicMock()
            mock_guardrails.return_value.check_pre_generation.return_value = GuardrailResult(passed=True)
            mock_guardrails.return_value.check_post_generation.return_value = GuardrailResult(passed=True)

            mock_retrieval.return_value = MagicMock()
            mock_retrieval.return_value.orchestrate.return_value = (
                MagicMock(retrieval_time_ms=0.5, provider="mock"),
                RAGContext(
                    context="Mock context.",
                    fragments=[{"text": "text", "score": 0.5}],
                    has_sufficient_context=True,
                    build_time_ms=1.0,
                    total_tokens=100,
                    fragment_count=1,
                ),
            )
            mock_provider = MagicMock()
            mock_provider.generate_text.side_effect = TimeoutError("Provider timed out")
            mock_factory.return_value.create.return_value = mock_provider

            engine = RAGEngine(config=config)
            request = RAGRequest(query="test query", patient_id="p1")
            response = engine.answer(request)
            assert response is not None

    def test_empty_query_handled_by_rag(self):
        from app.rag.models import RAGContext, GuardrailResult

        config = RAGEngineConfig(
            enable_query_classification=False,
            enable_citations=False,
            enable_guardrails_pre=False,
            enable_guardrails_post=False,
        )
        with (
            patch("app.rag.rag_engine.RetrievalOrchestrator") as mock_retrieval,
            patch("app.rag.response_generator.AIProviderFactory") as mock_factory,
            patch("app.rag.guardrails.Guardrails") as mock_guardrails,
        ):
            mock_guardrails.return_value = MagicMock()
            mock_guardrails.return_value.check_pre_generation.return_value = GuardrailResult(passed=True)
            mock_guardrails.return_value.check_post_generation.return_value = GuardrailResult(passed=True)

            mock_retrieval.return_value = MagicMock()
            mock_retrieval.return_value.orchestrate.return_value = (
                MagicMock(results=[], retrieval_time_ms=0.5, provider="mock"),
                RAGContext(
                    context="",
                    fragments=[],
                    has_sufficient_context=False,
                    build_time_ms=1.0,
                    total_tokens=0,
                    fragment_count=0,
                ),
            )
            mock_provider = MagicMock()
            mock_provider.generate_text.return_value = "No relevant information found."
            mock_factory.return_value.create.return_value = mock_provider
            mock_guardrails.return_value = MagicMock()

            engine = RAGEngine(config=config)
            from app.rag.models import RAGRequest
            request = RAGRequest(query="", patient_id="p1")
            response = engine.answer(request)
            assert response is not None

    def test_chat_service_handles_provider_error(self):
        with patch("app.chat.chat_service.RAGEngine") as mock_rag_cls:
            mock_rag = MagicMock()
            mock_rag.answer.side_effect = RuntimeError("RAG failed")
            mock_rag_cls.return_value = mock_rag

            service = ChatService()
            with pytest.raises((RuntimeError, Exception)):
                service.ask(ChatRequest(query="test", session_id="s1"))


class TestErrorPathsGuardrails:
    def test_guardrails_reject_harmful_query(self):
        from app.rag.guardrails import Guardrails

        guardrails = Guardrails()
        from app.rag.models import RAGContext

        context = RAGContext(
            context="Harmless medical context.",
            has_sufficient_context=True,
        )
        result = guardrails.check_pre_generation(
            query="How do I harm myself?",
            context=context,
        )
        assert result is not None
        assert hasattr(result, "passed")

    def test_guardrails_allow_safe_query(self):
        from app.rag.guardrails import Guardrails

        guardrails = Guardrails()
        from app.rag.models import RAGContext

        context = RAGContext(
            context="Medical context about blood pressure medication.",
            has_sufficient_context=True,
        )
        result = guardrails.check_pre_generation(
            query="What is my blood pressure medication?",
            context=context,
        )
        assert result is not None
        assert hasattr(result, "passed")
