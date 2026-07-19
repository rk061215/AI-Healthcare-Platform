from __future__ import annotations

import time
from typing import Any, Optional

from app.rag.citation_manager import CitationManager
from app.rag.config import RAGEngineConfig
from app.rag.exceptions import (
    EmptyQueryError,
    GuardrailError,
    QueryError,
    RAGError,
)
from app.rag.guardrails import Guardrails
from app.rag.models import (
    RAGContext,
    RAGMetrics,
    RAGRequest,
    RAGResponse,
)
from app.rag.query_classifier import QueryClassifier
from app.rag.query_processor import QueryProcessor
from app.rag.query_rewriter import BaseQueryRewriter, DefaultQueryRewriter
from app.rag.response_generator import ResponseGenerator
from app.rag.retrieval_orchestrator import RetrievalOrchestrator


class RAGEngine:
    """High-level RAG orchestration engine.

    Coordinates the complete RAG pipeline:
    Query → Process → Classify → (Rewrite) → Retrieve → Build Context →
    Guardrails (pre) → Generate → Guardrails (post) → Citations →
    Structured RAG Response

    Every stage is independently replaceable via dependency injection.
    No Conversation Memory, no LangGraph, no Chat UI.
    """

    def __init__(
        self,
        config: Optional[RAGEngineConfig] = None,
        query_processor: Optional[QueryProcessor] = None,
        query_classifier: Optional[QueryClassifier] = None,
        query_rewriter: Optional[BaseQueryRewriter] = None,
        retrieval_orchestrator: Optional[RetrievalOrchestrator] = None,
        response_generator: Optional[ResponseGenerator] = None,
        citation_manager: Optional[CitationManager] = None,
        guardrails: Optional[Guardrails] = None,
    ) -> None:
        self._config = config or RAGEngineConfig()

        self._query_processor = query_processor or QueryProcessor()
        self._query_classifier = query_classifier or QueryClassifier()
        self._query_rewriter = query_rewriter or DefaultQueryRewriter()
        self._retrieval_orchestrator = (
            retrieval_orchestrator or RetrievalOrchestrator(config=self._config)
        )
        self._response_generator = response_generator or ResponseGenerator(
            config=self._config
        )
        self._citation_manager = citation_manager or CitationManager()
        self._guardrails = guardrails or Guardrails()

    def answer(self, request: RAGRequest, document_text: Optional[str] = None) -> RAGResponse:
        """Execute the full RAG pipeline for a single query.

        Args:
            request: RAGRequest with query, patient_id, and optional parameters.

        Returns:
            RAGResponse with answer, citations, guardrail results, and metrics.
        """
        metrics = RAGMetrics()
        overall_start = time.perf_counter()

        try:
            # 1. Query Processing
            t0 = time.perf_counter()
            processed = self._query_processor.process(request.query)
            metrics.query_processing_ms = (time.perf_counter() - t0) * 1000

            # 2. Query Classification
            t0 = time.perf_counter()
            if self._config.enable_query_classification:
                classification = self._query_classifier.classify(
                    processed.normalized
                )
            else:
                from app.rag.models import QueryClassification as QC
                classification = QC(query_type="unknown")
            metrics.query_classification_ms = (time.perf_counter() - t0) * 1000
            metrics.query_type = classification.query_type

            # 3. Query Rewriting (optional)
            rewritten = processed.normalized
            if self._config.enable_query_rewriting:
                rewritten_result = self._query_rewriter.rewrite(
                    processed.normalized
                )
                rewritten = rewritten_result.rewritten

            top_k = (
                request.top_k
                or classification.suggested_top_k
                or self._config.top_k
            )

            # 4. Retrieval + Context Building
            retrieved, context = self._retrieval_orchestrator.orchestrate(
                query=rewritten,
                patient_id=request.patient_id,
                report_id=request.report_id,
                document_type=request.document_type,
                top_k=top_k,
                min_score=self._config.min_score,
                context_max_tokens=request.max_tokens or self._config.context_max_tokens,
                context_strategy=request.context_strategy or self._config.context_strategy,
                metadata_filter=request.metadata_filter or {},
            )
            metrics.retrieval_ms = retrieved.retrieval_time_ms
            metrics.context_build_ms = context.build_time_ms
            metrics.num_documents_retrieved = len(retrieved.results)
            metrics.num_fragments_in_context = context.fragment_count
            metrics.retrieval_provider = retrieved.provider
            metrics.truncated = context.total_tokens > 0

            if not context.has_sufficient_context and document_text:
                context = RAGContext(
                    context=document_text,
                    has_sufficient_context=True,
                    fragment_count=1,
                    build_time_ms=0.0,
                )
                metrics.num_fragments_in_context = 1

            if request.conversation_history:
                context.conversation_history = request.conversation_history

            # 5. Pre-generation Guardrails
            if self._config.enable_guardrails_pre:
                t0 = time.perf_counter()
                pre_result = self._guardrails.check_pre_generation(
                    query=request.query, context=context
                )
                metrics.guardrail_pre_ms = (time.perf_counter() - t0) * 1000
                if pre_result.failures:
                    return self._build_guardrail_failure(
                        request=request,
                        pre_result=pre_result,
                        context=context,
                        metrics=metrics,
                        overall_start=overall_start,
                    )
            else:
                pre_result = None

            # 6. Response Generation
            t0 = time.perf_counter()
            enable_citations = (
                request.enable_citations and self._config.enable_citations
            )
            answer = self._response_generator.generate(
                query=request.query,
                context=context,
                temperature=request.temperature or self._config.temperature,
                max_tokens=request.max_tokens or self._config.max_tokens,
            )
            metrics.generation_ms = (time.perf_counter() - t0) * 1000

            # 7. Post-generation Guardrails
            post_result: Optional[Any] = None
            if self._config.enable_guardrails_post:
                t0 = time.perf_counter()
                post_result = self._guardrails.check_post_generation(
                    response=answer,
                    context=context,
                    citations=self._citation_manager.extract_citations(context)
                    if enable_citations else None,
                )
                metrics.guardrail_post_ms = (time.perf_counter() - t0) * 1000
                if post_result.failures:
                    metrics.guardrails_triggered = True

            # 8. Citations
            t0 = time.perf_counter()
            if enable_citations:
                citation_block = self._citation_manager.extract_citations(context)
                metrics.citation_ms = (time.perf_counter() - t0) * 1000
                metrics.num_citations = citation_block.citation_count
            else:
                from app.rag.models import CitationBlock
                citation_block = CitationBlock()
                metrics.citation_ms = 0.0

            # 9. Apply safety disclaimer
            final_answer = self._guardrails.apply_safety_disclaimer(answer)

            metrics.total_duration_ms = (
                time.perf_counter() - overall_start
            ) * 1000
            metrics.llm_provider = self._config.provider

            combined_result = GuardrailResult(
                passed=True, warnings=[], failures=[]
            )
            if pre_result:
                combined_result.warnings.extend(pre_result.warnings)
            if post_result:
                combined_result.warnings.extend(post_result.warnings)

            from app.rag.models import GuardrailResult as GR
            guardrail_result = GR(
                passed=combined_result.passed,
                score=1.0 - len(combined_result.warnings) * 0.1,
                warnings=combined_result.warnings,
                failures=combined_result.failures,
                requires_human_review=metrics.guardrails_triggered,
            )

            return RAGResponse(
                answer=final_answer,
                citations=citation_block,
                query=request.query,
                query_type=classification.query_type,
                guardrail_result=guardrail_result,
                processing_time_ms=round(metrics.total_duration_ms, 2),
                model=self._config.model,
                provider=self._config.provider,
            )

        except (EmptyQueryError, QueryError) as exc:
            metrics.total_duration_ms = (
                time.perf_counter() - overall_start
            ) * 1000
            return RAGResponse(
                answer=f"I couldn't process your question: {exc}",
                query=request.query,
                processing_time_ms=round(metrics.total_duration_ms, 2),
                model=self._config.model,
                provider=self._config.provider,
            )
        except RAGError as exc:
            metrics.total_duration_ms = (
                time.perf_counter() - overall_start
            ) * 1000
            return RAGResponse(
                answer=f"I encountered an error processing your request: {exc}",
                query=request.query,
                processing_time_ms=round(metrics.total_duration_ms, 2),
                model=self._config.model,
                provider=self._config.provider,
            )

    def _build_guardrail_failure(
        self,
        request: RAGRequest,
        pre_result: Any,
        context: Any,
        metrics: RAGMetrics,
        overall_start: float,
    ) -> RAGResponse:
        metrics.total_duration_ms = (time.perf_counter() - overall_start) * 1000
        metrics.guardrails_triggered = True

        return RAGResponse(
            answer=(
                "I'm unable to answer this question with the available information. "
                + " ".join(pre_result.failures)
            ),
            query=request.query,
            guardrail_result=pre_result,
            processing_time_ms=round(metrics.total_duration_ms, 2),
            model=self._config.model,
            provider=self._config.provider,
        )

    @property
    def config(self) -> RAGEngineConfig:
        return self._config

    @property
    def retrieval_orchestrator(self) -> RetrievalOrchestrator:
        return self._retrieval_orchestrator

    @property
    def guardrails(self) -> Guardrails:
        return self._guardrails


from app.rag.models import GuardrailResult
