from __future__ import annotations

from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest

from app.rag.citation_manager import CitationManager
from app.rag.config import RAGEngineConfig
from app.rag.exceptions import (
    CitationError,
    ConfigurationError,
    ContextBuildError,
    EmptyQueryError,
    GuardrailError,
    InsufficientContextError,
    QueryClassificationError,
    QueryError,
    RAGError,
    ResponseGenerationError,
    RetrievalError,
    UnsafeContentError,
    UnsupportedQueryError,
)
from app.rag.guardrails import Guardrails
from app.rag.models import (
    CitationBlock,
    CitationEntry,
    GuardrailResult,
    ProcessedQuery,
    QueryClassification,
    RAGContext,
    RAGMetrics,
    RAGRequest,
    RAGResponse,
    RAG_SCHEMA_VERSION,
    RewrittenQuery,
)
from app.rag.query_classifier import CLASSIFICATION_PATTERNS, QueryClassifier
from app.rag.query_processor import QueryProcessor
from app.rag.query_rewriter import DefaultQueryRewriter
from app.rag.rag_engine import RAGEngine
from app.rag.response_generator import ResponseGenerator
from app.rag.retrieval_orchestrator import RetrievalOrchestrator


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_mock_citations() -> list[dict[str, Any]]:
    return [
        {
            "document_id": f"doc_{i}",
            "report_id": f"rep_{i}",
            "chunk_id": f"chunk_{i}",
            "section": "diagnosis" if i == 0 else "medication",
            "page": 1,
            "source": "ocr",
            "score": 0.9 - i * 0.1,
        }
        for i in range(3)
    ]


def make_mock_fragments() -> list[dict[str, Any]]:
    return [
        {
            "text": f"Fragment {i}: Patient has high blood pressure.",
            "score": 0.9 - i * 0.1,
            "citation": {
                "document_id": f"doc_{i}",
                "report_id": f"rep_{i}",
                "chunk_id": f"chunk_{i}",
                "section": "diagnosis" if i == 0 else "medication",
                "page": 1,
                "source": "ocr",
            },
            "rank": i,
        }
        for i in range(3)
    ]


def make_mock_context(
    text: str = "Patient has high blood pressure. Prescribed lisinopril 10mg daily.",
    fragment_count: int = 3,
) -> RAGContext:
    fragments = make_mock_fragments()[:fragment_count]
    return RAGContext(
        context=text,
        fragments=fragments,
        citations=make_mock_citations()[:fragment_count],
        has_sufficient_context=True,
        fragment_count=fragment_count,
    )


# ─────────────────────────────────────────────
# Tests: Config
# ─────────────────────────────────────────────

class TestRAGEngineConfig:
    def test_default_values(self):
        config = RAGEngineConfig()
        assert config.provider == "gemini"
        assert config.top_k == 10
        assert config.temperature == 0.3

    def test_model_default(self):
        config = RAGEngineConfig()
        assert config.model == "gemini-2.0-flash"

    def test_provided_values(self):
        config = RAGEngineConfig(
            provider="test", model="test-model", top_k=25
        )
        assert config.provider == "test"
        assert config.model == "test-model"
        assert config.top_k == 25


# ─────────────────────────────────────────────
# Tests: Exceptions
# ─────────────────────────────────────────────

class TestRAGExceptions:
    def test_exception_hierarchy(self):
        assert issubclass(RAGError, Exception)
        assert issubclass(ConfigurationError, RAGError)
        assert issubclass(QueryError, RAGError)
        assert issubclass(EmptyQueryError, QueryError)
        assert issubclass(QueryClassificationError, RAGError)
        assert issubclass(UnsupportedQueryError, QueryClassificationError)
        assert issubclass(RetrievalError, RAGError)
        assert issubclass(ContextBuildError, RAGError)
        assert issubclass(InsufficientContextError, RAGError)
        assert issubclass(ResponseGenerationError, RAGError)
        assert issubclass(GuardrailError, RAGError)
        assert issubclass(UnsafeContentError, GuardrailError)
        assert issubclass(CitationError, RAGError)

    def test_exception_messages(self):
        exc = RAGError("test error")
        assert str(exc) == "test error"


# ─────────────────────────────────────────────
# Tests: Models
# ─────────────────────────────────────────────

class TestRAGModels:
    def test_rag_response_defaults(self):
        resp = RAGResponse()
        assert resp.answer == ""
        assert resp.query == ""
        assert resp.schema_version == RAG_SCHEMA_VERSION

    def test_rag_response_with_values(self):
        resp = RAGResponse(
            answer="Test answer",
            query="Test query",
            query_type="medication",
            processing_time_ms=100.0,
            model="test-model",
            provider="test-provider",
        )
        assert resp.answer == "Test answer"
        assert resp.query == "Test query"
        assert resp.query_type == "medication"
        assert resp.processing_time_ms == 100.0

    def test_rag_request_defaults(self):
        req = RAGRequest(query="What is my diagnosis?")
        assert req.query == "What is my diagnosis?"
        assert req.enable_guardrails is True
        assert req.enable_citations is True

    def test_rag_metrics_defaults(self):
        metrics = RAGMetrics()
        assert metrics.total_duration_ms == 0.0
        assert metrics.query_type == "unknown"

    def test_guardrail_result_defaults(self):
        result = GuardrailResult()
        assert result.passed is True
        assert result.score == 1.0
        assert result.warnings == []
        assert result.failures == []

    def test_citation_entry(self):
        entry = CitationEntry(
            citation_id=1,
            document_id="doc_1",
            chunk_id="chunk_1",
        )
        assert entry.citation_id == 1
        assert entry.document_id == "doc_1"

    def test_citation_block(self):
        block = CitationBlock()
        assert block.citations == []
        assert block.citation_count == 0

    def test_query_classification(self):
        qc = QueryClassification(
            query_type="medication",
            confidence=0.85,
            suggested_sections=["medication", "plan"],
        )
        assert qc.query_type == "medication"
        assert qc.confidence == 0.85

    def test_processed_query(self):
        pq = ProcessedQuery(
            original="What medication?",
            normalized="what medication",
            cleaned="What medication",
        )
        assert pq.original == "What medication?"
        assert pq.has_medical_terms is False

    def test_rewritten_query(self):
        rq = RewrittenQuery(
            original="rx",
            rewritten="prescription",
            strategy="expansion",
        )
        assert rq.original == "rx"
        assert rq.rewritten == "prescription"


# ─────────────────────────────────────────────
# Tests: Query Processor
# ─────────────────────────────────────────────

class TestQueryProcessor:
    def test_empty_query_raises(self):
        proc = QueryProcessor()
        with pytest.raises(EmptyQueryError):
            proc.process("")
        with pytest.raises(EmptyQueryError):
            proc.process("   ")

    def test_normalization(self):
        proc = QueryProcessor()
        result = proc.process("What IS my   Diagnosis?")
        assert result.normalized == "what is my diagnosis"
        assert result.original == "What IS my   Diagnosis?"

    def test_medical_term_detection(self):
        proc = QueryProcessor()
        result = proc.process("What is my diagnosis and medication?")
        assert result.has_medical_terms is True
        assert "diagnosis" in result.detected_entities
        assert "medication" in result.detected_entities

    def test_no_medical_terms(self):
        proc = QueryProcessor()
        result = proc.process("What is the weather today?")
        assert result.has_medical_terms is False

    def test_word_count(self):
        proc = QueryProcessor()
        result = proc.process("What is my blood pressure?")
        assert result.word_count == 5

    def test_cleaning_removes_special_chars(self):
        proc = QueryProcessor()
        result = proc.process("What!! is my @diagnosis?")
        assert "@" not in result.cleaned


# ─────────────────────────────────────────────
# Tests: Query Classifier
# ─────────────────────────────────────────────

class TestQueryClassifier:
    def test_medication_classification(self):
        classifier = QueryClassifier()
        result = classifier.classify("What is my medication dosage?")
        assert result.query_type == "medication"
        assert result.confidence > 0

    def test_lab_result_classification(self):
        classifier = QueryClassifier()
        result = classifier.classify("What do my blood test results mean?")
        assert result.query_type == "lab_result"

    def test_diagnosis_classification(self):
        classifier = QueryClassifier()
        result = classifier.classify("What is my diagnosis?")
        assert result.query_type == "diagnosis"

    def test_follow_up_classification(self):
        classifier = QueryClassifier()
        result = classifier.classify("When is my next appointment?")
        assert result.query_type == "follow_up"

    def test_patient_metadata_classification(self):
        classifier = QueryClassifier()
        result = classifier.classify("What is my date of birth?")
        assert result.query_type == "patient_metadata"

    def test_general_medical_classification(self):
        classifier = QueryClassifier()
        result = classifier.classify("Explain how insulin works in the body")
        assert result.query_type == "general_medical"

    def test_unknown_classification(self):
        classifier = QueryClassifier()
        result = classifier.classify("How many people live in France?")
        assert result.query_type == "unknown"

    def test_empty_query_raises(self):
        classifier = QueryClassifier()
        with pytest.raises(QueryClassificationError):
            classifier.classify("")

    def test_classification_patterns_exist(self):
        assert "medication" in CLASSIFICATION_PATTERNS
        assert "lab_result" in CLASSIFICATION_PATTERNS
        assert "diagnosis" in CLASSIFICATION_PATTERNS
        assert "follow_up" in CLASSIFICATION_PATTERNS
        assert "patient_metadata" in CLASSIFICATION_PATTERNS
        assert "general_medical" in CLASSIFICATION_PATTERNS


# ─────────────────────────────────────────────
# Tests: Query Rewriter
# ─────────────────────────────────────────────

class TestDefaultQueryRewriter:
    def test_no_rewrite_needed(self):
        rewriter = DefaultQueryRewriter(add_synonyms=False)
        result = rewriter.rewrite("What is my diagnosis?")
        assert result.strategy == "none"
        assert result.rewritten == "What is my diagnosis?"

    def test_abbreviation_expansion(self):
        rewriter = DefaultQueryRewriter()
        result = rewriter.rewrite("What is my rx?")
        assert "prescription" in result.rewritten
        assert result.strategy != "none"

    def test_multiple_abbreviations(self):
        rewriter = DefaultQueryRewriter()
        result = rewriter.rewrite("The dx and rx")
        assert "diagnosis" in result.rewritten
        assert "prescription" in result.rewritten

    def test_empty_query(self):
        rewriter = DefaultQueryRewriter()
        result = rewriter.rewrite("")
        assert result.strategy == "none"

    def test_disabled_expansion(self):
        rewriter = DefaultQueryRewriter(expand_abbreviations=False, add_synonyms=False)
        result = rewriter.rewrite("What is my rx?")
        assert "rx" in result.rewritten
        assert result.strategy == "none"


# ─────────────────────────────────────────────
# Tests: Retrieval Orchestrator
# ─────────────────────────────────────────────

class TestRetrievalOrchestrator:
    def test_initialization(self):
        config = RAGEngineConfig(top_k=5)
        mock_retriever = MagicMock()
        orch = RetrievalOrchestrator(config=config, retriever_service=mock_retriever)
        assert orch is not None

    def test_orchestrate_empty_retrieval(self):
        mock_retriever = MagicMock()
        mock_retriever.search.return_value = MagicMock(
            results=[],
            retrieval_time_ms=0.0,
            provider="mock",
        )

        config = RAGEngineConfig(top_k=5)
        orch = RetrievalOrchestrator(
            config=config,
            retriever_service=mock_retriever,
        )
        retrieved, context = orch.orchestrate(query="test query")
        assert context.has_sufficient_context is False
        assert context.context == ""

    def test_orchestrate_with_results(self):
        from app.retrieval.models import RetrievedDocument, RetrievalQuery, RetrievalResult

        mock_retriever = MagicMock()
        mock_result = MagicMock()
        mock_result.results = [
            RetrievalResult(
                chunk_id=f"chunk_{i}",
                text=f"Test document {i}",
                score=0.9 - i * 0.1,
                document_id=f"doc_{i}",
                report_id=f"rep_{i}",
                section="diagnosis",
            )
            for i in range(3)
        ]
        mock_result.retrieval_time_ms = 10.0
        mock_result.provider = "mock"
        mock_retriever.search.return_value = mock_result

        config = RAGEngineConfig(top_k=5)
        orch = RetrievalOrchestrator(
            config=config,
            retriever_service=mock_retriever,
        )
        retrieved, context = orch.orchestrate(query="test query")
        assert context.has_sufficient_context is True
        assert len(context.fragments) > 0


# ─────────────────────────────────────────────
# Tests: Citation Manager
# ─────────────────────────────────────────────

class TestCitationManager:
    def test_extract_citations(self):
        mgr = CitationManager()
        context = make_mock_context(fragment_count=2)
        block = mgr.extract_citations(context)
        assert block.citation_count == 2
        assert len(block.citations) == 2

    def test_extract_citations_empty(self):
        mgr = CitationManager()
        context = RAGContext(context="", citations=[], has_sufficient_context=False)
        block = mgr.extract_citations(context)
        assert block.citation_count == 0

    def test_deduplication(self):
        mgr = CitationManager()
        context = RAGContext(
            context="test",
            citations=[
                {
                    "document_id": "doc_1",
                    "chunk_id": "chunk_1",
                    "section": "diagnosis",
                },
                {
                    "document_id": "doc_1",
                    "chunk_id": "chunk_1",
                    "section": "diagnosis",
                },
            ],
            has_sufficient_context=True,
            fragment_count=2,
        )
        block = mgr.extract_citations(context)
        assert block.citation_count == 1

    def test_hallucinated_citations(self):
        mgr = CitationManager()
        context = make_mock_context(fragment_count=2)
        block = mgr.extract_citations(context)

        response = "Based on [citation:1] and [citation:99]"
        hallucinated = mgr.has_hallucinated_citations(response, block)
        assert len(hallucinated) == 1
        assert hallucinated[0]["cited_id"] == "99"

    def test_no_hallucinations(self):
        mgr = CitationManager()
        context = make_mock_context(fragment_count=2)
        block = mgr.extract_citations(context)

        response = "Based on [citation:1] and [citation:2]"
        hallucinated = mgr.has_hallucinated_citations(response, block)
        assert len(hallucinated) == 0

    def test_validate_response_grounding(self):
        mgr = CitationManager()
        context = make_mock_context(fragment_count=2)
        block = mgr.extract_citations(context)

        result = mgr.validate_response_grounding(
            "See [citation:1] and [citation:99]", block
        )
        assert result["is_grounded"] is False
        assert result["hallucinated_count"] == 1

    def test_format_block(self):
        mgr = CitationManager()
        context = make_mock_context(fragment_count=1)
        block = mgr.extract_citations(context)
        assert "Sources" in block.formatted_block


# ─────────────────────────────────────────────
# Tests: Guardrails
# ─────────────────────────────────────────────

class TestGuardrails:
    def test_pre_gen_sufficient_context(self):
        g = Guardrails()
        context = make_mock_context(fragment_count=3)
        result = g.check_pre_generation("test query", context)
        assert result.passed is True

    def test_pre_gen_no_context(self):
        g = Guardrails()
        context = RAGContext(context="", has_sufficient_context=False)
        result = g.check_pre_generation("test query", context)
        assert result.passed is False
        assert len(result.failures) > 0

    def test_pre_gen_query_safety_harmful(self):
        g = Guardrails()
        context = make_mock_context(fragment_count=1)
        result = g.check_pre_generation("how to harm myself", context)
        assert result.passed is False

    def test_post_gen_diagnostic_language(self):
        g = Guardrails()
        context = make_mock_context()
        result = g.check_post_generation(
            "You have diabetes and you should take metformin", context
        )
        assert result.passed is True
        assert len(result.warnings) > 0

    def test_post_gen_treatment_recommendation(self):
        g = Guardrails()
        context = make_mock_context()
        result = g.check_post_generation(
            "You should take lisinopril 10mg", context
        )
        assert result.passed is True
        assert len(result.warnings) > 0

    def test_post_gen_hallucinated_citation(self):
        g = Guardrails()
        context = make_mock_context()
        mock_citations = MagicMock()
        mock_citations.citations = [
            MagicMock(citation_id="1"),
            MagicMock(citation_id="2"),
        ]

        result = g.check_post_generation(
            "See [citation:1] and [citation:99]",
            context,
            citations=mock_citations,
        )
        assert result.passed is False
        assert len(result.failures) > 0

    def test_post_gen_valid_citations(self):
        g = Guardrails()
        context = make_mock_context()
        mock_citations = MagicMock()
        mock_citations.citations = [
            MagicMock(citation_id="1"),
            MagicMock(citation_id="2"),
        ]

        result = g.check_post_generation(
            "See [citation:1] and [citation:2]",
            context,
            citations=mock_citations,
        )
        assert result.passed is True

    def test_apply_disclaimer(self):
        g = Guardrails()
        result = g.apply_safety_disclaimer("Take your medicine")
        assert "IMPORTANT" in result
        assert "consult your healthcare provider" in result


# ─────────────────────────────────────────────
# Tests: Response Generator
# ─────────────────────────────────────────────

class TestResponseGenerator:
    def test_generate_with_mock_provider(self):
        mock_provider = MagicMock()
        mock_provider.generate_text.return_value = "Your medication is lisinopril 10mg."

        config = RAGEngineConfig()
        gen = ResponseGenerator(config=config, provider=mock_provider)
        context = make_mock_context()
        response = gen.generate("What medication?", context)
        assert "lisinopril" in response

    def test_generate_handles_provider_error(self):
        mock_provider = MagicMock()
        mock_provider.generate_text.side_effect = RuntimeError("API error")

        config = RAGEngineConfig()
        gen = ResponseGenerator(config=config, provider=mock_provider)
        context = make_mock_context()
        with pytest.raises(ResponseGenerationError):
            gen.generate("What medication?", context)

    def test_build_prompt_includes_context(self):
        mock_provider = MagicMock()
        gen = ResponseGenerator(config=RAGEngineConfig(), provider=mock_provider)
        context = make_mock_context(text="Patient has diabetes.")
        prompt = gen._build_prompt("What diagnosis?", context)
        assert "Patient has diabetes" in prompt
        assert "What diagnosis?" in prompt


# ─────────────────────────────────────────────
# Tests: RAG Engine (End-to-End)
# ─────────────────────────────────────────────

class TestRAGEngine:
    def test_initialization(self):
        engine = RAGEngine(
            retrieval_orchestrator=MagicMock(),
            response_generator=MagicMock(),
        )
        assert engine is not None
        assert engine.config.provider == "gemini"

    def test_custom_config(self):
        config = RAGEngineConfig(provider="test", model="test-model")
        engine = RAGEngine(
            config=config,
            retrieval_orchestrator=MagicMock(),
            response_generator=MagicMock(),
        )
        assert engine.config.provider == "test"

    def test_answer_with_mock_components(self):
        mock_processor = MagicMock()
        mock_processor.process.return_value = ProcessedQuery(
            original="What medication?",
            normalized="what medication",
            cleaned="What medication",
            has_medical_terms=True,
            word_count=2,
            detected_entities=["medication"],
        )

        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = QueryClassification(
            query_type="medication",
            confidence=0.9,
            suggested_top_k=15,
            suggested_sections=["medication"],
        )

        mock_retrieved = MagicMock()
        mock_retrieved.results = []
        mock_retrieved.retrieval_time_ms = 5.0
        mock_retrieved.provider = "mock"

        mock_orchestrator = MagicMock()
        mock_orchestrator.orchestrate.return_value = (
            mock_retrieved,
            make_mock_context(fragment_count=2),
        )

        mock_generator = MagicMock()
        mock_generator.generate.return_value = (
            "Your medication is lisinopril 10mg daily."
        )

        config = RAGEngineConfig(enable_citations=False, enable_guardrails_pre=False, enable_guardrails_post=False)
        engine = RAGEngine(
            config=config,
            query_processor=mock_processor,
            query_classifier=mock_classifier,
            retrieval_orchestrator=mock_orchestrator,
            response_generator=mock_generator,
        )

        request = RAGRequest(query="What medication?")
        response = engine.answer(request)
        assert response.answer is not None
        assert len(response.answer) > 0

    def test_empty_query_handling(self):
        engine = RAGEngine(
            retrieval_orchestrator=MagicMock(),
            response_generator=MagicMock(),
        )
        request = RAGRequest(query="")
        response = engine.answer(request)
        assert "couldn't process" in response.answer.lower()

    def test_short_query_after_processing(self):
        engine = RAGEngine(
            retrieval_orchestrator=MagicMock(),
            response_generator=MagicMock(),
        )
        request = RAGRequest(query="a")
        response = engine.answer(request)
        assert "couldn't process" in response.answer.lower()

    def test_guardrail_prevention(self):
        mock_guardrails = MagicMock()
        mock_guardrails.check_pre_generation.return_value = GuardrailResult(
            passed=False,
            score=0.0,
            failures=["No context available to answer the query"],
        )

        config = RAGEngineConfig(enable_citations=False, enable_guardrails_pre=True, enable_guardrails_post=False)

        mock_orchestrator = MagicMock()
        mock_retrieved = MagicMock()
        mock_retrieved.results = []
        mock_retrieved.retrieval_time_ms = 0.0
        mock_retrieved.provider = "mock"
        mock_orchestrator.orchestrate.return_value = (
            mock_retrieved,
            make_mock_context(),
        )

        mock_generator = MagicMock()

        engine = RAGEngine(
            config=config,
            retrieval_orchestrator=mock_orchestrator,
            response_generator=mock_generator,
            guardrails=mock_guardrails,
        )
        request = RAGRequest(query="What is my diagnosis?")
        response = engine.answer(request)
        assert response.guardrail_result is not None
        assert not response.guardrail_result.passed


# ─────────────────────────────────────────────
# Tests: RAG Engine Error Handling
# ─────────────────────────────────────────────

class TestRAGEngineErrorHandling:
    def test_retrieval_failure(self):
        mock_orchestrator = MagicMock()
        mock_orchestrator.orchestrate.side_effect = RetrievalError("DB down")

        mock_generator = MagicMock()

        config = RAGEngineConfig(enable_guardrails_pre=False)
        engine = RAGEngine(
            config=config,
            retrieval_orchestrator=mock_orchestrator,
            response_generator=mock_generator,
        )
        request = RAGRequest(query="What is my diagnosis?")
        response = engine.answer(request)
        assert "error" in response.answer.lower()

    def test_context_build_failure(self):
        mock_orchestrator = MagicMock()
        mock_orchestrator.orchestrate.side_effect = ContextBuildError(
            "Context assembly failed"
        )

        mock_generator = MagicMock()

        config = RAGEngineConfig(enable_guardrails_pre=False)
        engine = RAGEngine(
            config=config,
            retrieval_orchestrator=mock_orchestrator,
            response_generator=mock_generator,
        )
        request = RAGRequest(query="What is my diagnosis?")
        response = engine.answer(request)
        assert "error" in response.answer.lower()


# ─────────────────────────────────────────────
# Tests: Edge Cases
# ─────────────────────────────────────────────

class TestEdgeCases:
    def test_single_word_query(self):
        processor = QueryProcessor()
        result = processor.process("Medication")
        assert result.word_count == 1
        assert result.has_medical_terms is True

    def test_query_with_numbers(self):
        processor = QueryProcessor()
        result = processor.process("What does 120/80 blood pressure mean?")
        assert result.has_medical_terms is True

    def test_classification_with_multiple_matches(self):
        classifier = QueryClassifier()
        result = classifier.classify("What is my diagnosis and medication?")
        assert result.query_type == "medication" or result.query_type == "diagnosis"
        assert result.confidence > 0

    def test_rewriter_with_mixed_content(self):
        rewriter = DefaultQueryRewriter()
        result = rewriter.rewrite("What is the rx for my dx?")
        assert "prescription" in result.rewritten
        assert "diagnosis" in result.rewritten

    def test_guardrails_very_short_response(self):
        g = Guardrails()
        context = make_mock_context()
        result = g.check_post_generation("Yes", context)
        assert result.passed is True

    def test_citation_format_special_chars(self):
        mgr = CitationManager()
        context = make_mock_context(fragment_count=1)
        block = mgr.extract_citations(context)
        assert block.citation_count == 1

    def test_empty_fragments_in_context(self):
        context = RAGContext(
            context="",
            fragments=[],
            citations=[],
            has_sufficient_context=False,
        )
        mgr = CitationManager()
        block = mgr.extract_citations(context)
        assert block.citation_count == 0

    def test_disabled_guardrails(self):
        config = RAGEngineConfig(
            enable_guardrails_pre=False,
            enable_guardrails_post=False,
            enable_citations=False,
        )

        mock_processor = MagicMock()
        mock_processor.process.return_value = ProcessedQuery(
            original="test", normalized="test", cleaned="test"
        )
        mock_classifier = MagicMock()
        mock_classifier.classify.return_value = QueryClassification(query_type="unknown")

        mock_retrieved = MagicMock()
        mock_retrieved.results = []
        mock_retrieved.retrieval_time_ms = 0.0
        mock_retrieved.provider = "mock"

        mock_orchestrator = MagicMock()
        mock_orchestrator.orchestrate.return_value = (
            mock_retrieved,
            make_mock_context(fragment_count=1),
        )

        mock_generator = MagicMock()
        mock_generator.generate.return_value = "Test response."

        engine = RAGEngine(
            config=config,
            query_processor=mock_processor,
            query_classifier=mock_classifier,
            retrieval_orchestrator=mock_orchestrator,
            response_generator=mock_generator,
        )

        request = RAGRequest(query="test")
        response = engine.answer(request)
        assert response.answer is not None


# ─────────────────────────────────────────────
# Tests: Exports
# ─────────────────────────────────────────────

class TestRAGExports:
    def test_module_imports(self):
        from app.rag import RAGEngine, RAGEngineConfig, RAGRequest, RAGResponse
        assert RAGEngine is not None
        assert RAGEngineConfig is not None
        assert RAGRequest is not None
        assert RAGResponse is not None

    def test_schema_version(self):
        assert RAG_SCHEMA_VERSION == "1.0.0"
