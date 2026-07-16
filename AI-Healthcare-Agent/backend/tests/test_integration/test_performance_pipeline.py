from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from app.chat.chat_service import ChatService
from app.chat.models import ChatRequest
from app.context.config import ContextConfig
from app.context.context_builder import ContextBuilder
from app.document_pipeline import DocumentPipeline, DocumentPipelineConfig
from app.embeddings.embedding_service import EmbeddingService
from app.memory.memory_service import MemoryService
from app.memory.config import MemoryConfig
from app.rag.models import RAGResponse
from app.rag.rag_engine import RAGEngine, RAGEngineConfig
from app.retrieval.retriever_service import RetrieverService
from app.tools.tool_service import ToolService
from app.vector_store.vector_service import VectorService


@pytest.fixture
def perf_rag_config() -> RAGEngineConfig:
    return RAGEngineConfig(
        enable_query_classification=True,
        enable_citations=True,
        enable_guardrails_pre=True,
        enable_guardrails_post=True,
        top_k=5,
        provider="gemini",
    )


class TestPerformanceBaseline:
    """Measure latency for every subsystem and establish a baseline."""

    SAMPLE_TEXT = (
        "Patient Name: John Doe\nDiagnosis: Hypertension\n"
        "Medications:\nLisinopril 10mg once daily\n"
        "Metformin 500mg twice daily\n"
        "Lab Results:\nBlood Glucose 126 mg/dL\nHbA1c 7.2 %"
    )

    def test_ocr_latency(self, sample_ocr_text):
        from app.ocr.engine import OcrEngine

        engine = OcrEngine(use_mock=True)

        import tempfile
        from pathlib import Path
        from PIL import Image

        tmp = Path(tempfile.mkdtemp()) / "perf_test.png"
        img = Image.new("RGB", (200, 60), color="white")
        img.save(tmp)

        trials = 3
        times = []
        for _ in range(trials):
            t0 = time.perf_counter()
            engine.process_document(tmp, "png")
            times.append((time.perf_counter() - t0) * 1000)

        avg = sum(times) / len(times)
        print(f"\n  OCR latency (mock): {avg:.1f}ms avg across {trials} runs")
        assert avg < 5000, f"OCR too slow: {avg:.1f}ms"

    def test_embedding_latency(self, mock_embedding_service):
        texts = [
            "Lisinopril 10mg for hypertension",
            "Metformin 500mg for diabetes",
            "HbA1c 7.2 percent",
        ]

        trials = 5
        times = []
        for _ in range(trials):
            t0 = time.perf_counter()
            mock_embedding_service.embed_batch(texts)
            times.append((time.perf_counter() - t0) * 1000)

        avg = sum(times) / len(times)
        print(f"\n  Embedding latency (mock): {avg:.1f}ms avg across {trials} runs")
        assert avg < 2000, f"Embedding too slow: {avg:.1f}ms"

    def test_vector_search_latency(self, mock_vector_store, mock_embedding_service):
        vs = VectorService(store=mock_vector_store, embedding_service=mock_embedding_service)
        vs.index_text("Lisinopril 10mg for hypertension", doc_id="d1")
        vs.index_text("Metformin 500mg twice daily", doc_id="d2")

        trials = 10
        times = []
        for _ in range(trials):
            t0 = time.perf_counter()
            vs.search("blood pressure medication", k=5)
            times.append((time.perf_counter() - t0) * 1000)

        avg = sum(times) / len(times)
        print(f"\n  Vector search latency (mock): {avg:.1f}ms avg across {trials} runs")
        assert avg < 500, f"Vector search too slow: {avg:.1f}ms"

    def test_context_builder_latency(self):
        builder = ContextBuilder(config=ContextConfig(max_tokens=2000))
        from app.retrieval.models import RetrievalQuery, RetrievalResult, RetrievedDocument

        q = RetrievalQuery(text="What medicines?")
        retrieved = RetrievedDocument(
            query=q,
            results=[
                RetrievalResult(
                    chunk_id="c1", text="Lisinopril 10mg once daily",
                    score=0.85, document_id="d1", patient_id="p1",
                    metadata={"section": "medication"},
                ),
                RetrievalResult(
                    chunk_id="c2", text="Metformin 500mg twice daily with meals",
                    score=0.72, document_id="d2", patient_id="p1",
                    metadata={"section": "medication"},
                ),
            ],
        )

        trials = 10
        times = []
        for _ in range(trials):
            t0 = time.perf_counter()
            builder.build(retrieved=retrieved)
            times.append((time.perf_counter() - t0) * 1000)

        avg = sum(times) / len(times)
        print(f"\n  Context Builder latency: {avg:.1f}ms avg across {trials} runs")
        assert avg < 500, f"Context Builder too slow: {avg:.1f}ms"

    def test_rag_latency(self, perf_rag_config):
        from app.rag.models import RAGContext, GuardrailResult, RAGRequest

        with (
            patch("app.rag.rag_engine.RetrievalOrchestrator") as mock_retrieval,
            patch("app.rag.response_generator.AIProviderFactory") as mock_factory,
        ):
            mock_retrieval.return_value = MagicMock()
            mock_retrieval.return_value.orchestrate.return_value = (
                MagicMock(results=[], retrieval_time_ms=0.5, provider="mock"),
                RAGContext(
                    context="Mock context about Lisinopril 10mg.",
                    fragments=[{"text": "Lisinopril 10mg", "score": 0.85}],
                    has_sufficient_context=True,
                    build_time_ms=1.0,
                    total_tokens=100,
                    fragment_count=1,
                ),
            )
            mock_provider = MagicMock()
            mock_provider.generate_text.return_value = (
                "Based on records, Lisinopril 10mg is prescribed."
            )
            mock_factory.return_value.create.return_value = mock_provider

            engine = RAGEngine(config=perf_rag_config)

            trials = 5
            times = []
            for _ in range(trials):
                t0 = time.perf_counter()
                engine.answer(RAGRequest(query="What is Lisinopril?", patient_id="p1"))
                times.append((time.perf_counter() - t0) * 1000)

            avg = sum(times) / len(times)
            print(f"\n  RAG engine latency (mocked): {avg:.1f}ms avg across {trials} runs")
            assert avg < 5000, f"RAG too slow: {avg:.1f}ms"

    def test_tool_execution_latency(self):
        service = ToolService()

        trials = 10
        times = []
        for _ in range(trials):
            t0 = time.perf_counter()
            service.run(
                tool_type="appointment",
                action="list",
                user_id="u1",
                user_role="patient",
                patient_id="p1",
                parameters={"patient_id": "p1"},
            )
            times.append((time.perf_counter() - t0) * 1000)

        avg = sum(times) / len(times)
        print(f"\n  Tool execution latency: {avg:.1f}ms avg across {trials} runs")
        assert avg < 1000, f"Tool execution too slow: {avg:.1f}ms"

    def test_memory_retrieval_latency(self):
        service = MemoryService(config=MemoryConfig(
            provider="in_memory", max_memories_per_session=50,
            enable_expiry_policy=False, enable_retention_policy=False,
        ))
        session_id = "perf-mem-session"
        for i in range(20):
            service.extract_from_chat(
                session_id=session_id,
                query=f"Q{i}", answer=f"A{i}",
                turn_number=i,
            )

        trials = 20
        times = []
        for _ in range(trials):
            t0 = time.perf_counter()
            service.recall(session_id)
            times.append((time.perf_counter() - t0) * 1000)

        avg = sum(times) / len(times)
        print(f"\n  Memory retrieval latency: {avg:.3f}ms avg across {trials} runs")
        assert avg < 100, f"Memory retrieval too slow: {avg:.3f}ms"

    def test_end_to_end_response_time(self):
        with (
            patch("app.chat.chat_service.RAGEngine") as mock_rag_cls,
            patch("app.chat.chat_service.ConfidenceCalculator") as mock_conf_cls,
        ):
            mock_rag = MagicMock()
            mock_rag.answer.return_value = RAGResponse(
                answer="Lisinopril 10mg daily for hypertension.",
                query_type="medication",
            )
            mock_rag_cls.return_value = mock_rag

            from app.chat.models import ConfidenceScore, ConfidenceLevel
            mock_conf = MagicMock()
            mock_conf.calculate.return_value = ConfidenceScore(
                overall=0.85, level=ConfidenceLevel.high,
                retrieval_score=0.85, chunk_count=2,
                citation_coverage=0.5, guardrail_validated=True,
                insufficient_evidence=False,
            )
            mock_conf_cls.return_value = mock_conf

            service = ChatService()
            trials = 5
            times = []
            for _ in range(trials):
                t0 = time.perf_counter()
                service.ask(ChatRequest(
                    query="What medicines are prescribed?",
                    session_id="perf-e2e",
                ))
                times.append((time.perf_counter() - t0) * 1000)

            avg = sum(times) / len(times)
            print(f"\n  End-to-end ChatService latency (mocked): {avg:.1f}ms avg across {trials} runs")
            assert avg < 5000, f"E2E too slow: {avg:.1f}ms"

    def test_document_pipeline_latency(self, sample_ocr_text):
        pipeline = DocumentPipeline(
            config=DocumentPipelineConfig(chunk_size=200, chunk_overlap=20),
        )

        trials = 10
        times = []
        for _ in range(trials):
            t0 = time.perf_counter()
            pipeline.process(
                raw_text=sample_ocr_text,
                patient_id="p1",
                report_id="r1",
                source="ocr",
            )
            times.append((time.perf_counter() - t0) * 1000)

        avg = sum(times) / len(times)
        print(f"\n  Document pipeline latency: {avg:.1f}ms avg across {trials} runs")
        assert avg < 500, f"Document pipeline too slow: {avg:.1f}ms"


class TestPerformanceReport:
    """Aggregate results and print a unified performance report."""

    @pytest.fixture(scope="class", autouse=True)
    def _capture_results(self, request):
        request.cls.results = {}
        yield

    def test_generate_report(self):
        print("\n\n==============================================")
        print("        PERFORMANCE BASELINE REPORT")
        print("==============================================")
        print(f"  Test suite: integration/performance")
        print(f"  Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Environment: mock providers")
        print("==============================================")
