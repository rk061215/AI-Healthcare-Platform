from __future__ import annotations

import time
from typing import Any, Optional

from app.context.config import ContextConfig
from app.context.context_builder import ContextBuilder
from app.rag.config import RAGEngineConfig
from app.rag.exceptions import ContextBuildError, RetrievalError
from app.rag.models import RAGContext, RAGMetrics
from app.retrieval.config import RetrieverConfig
from app.retrieval.models import RetrievedDocument
from app.retrieval.retriever_factory import RetrieverFactory
from app.retrieval.retriever_service import RetrieverService


class RetrievalOrchestrator:
    """Coordinates the retrieval pipeline: Retriever + Context Builder.

    Wires RetrieverService and ContextBuilder together so the RAG Engine
    only needs to call orchestrate() and receive structured context.
    """

    def __init__(
        self,
        config: Optional[RAGEngineConfig] = None,
        retriever_service: Optional[RetrieverService] = None,
        context_builder: Optional[ContextBuilder] = None,
    ) -> None:
        self._config = config or RAGEngineConfig()

        if retriever_service:
            self._retriever = retriever_service
        else:
            retriever_config = RetrieverConfig(
                provider=self._config.retrieval_provider,
                top_k=self._config.top_k,
                min_score_threshold=self._config.min_score,
            )
            retriever = RetrieverFactory.create(config=retriever_config)
            retriever.initialize()
            self._retriever = RetrieverService(retriever=retriever)

        if context_builder:
            self._context_builder = context_builder
        else:
            ctx_config = ContextConfig(
                max_tokens=self._config.context_max_tokens,
                strategy=self._config.context_strategy,
                priority_sections=self._config.priority_sections,
            )
            self._context_builder = ContextBuilder(config=ctx_config)

    def orchestrate(
        self,
        query: str,
        patient_id: Optional[str] = None,
        report_id: Optional[str] = None,
        document_type: Optional[str] = None,
        top_k: Optional[int] = None,
        min_score: float = 0.0,
        context_max_tokens: Optional[int] = None,
        context_strategy: Optional[str] = None,
        metadata_filter: Optional[dict[str, Any]] = None,
    ) -> tuple[RetrievedDocument, RAGContext]:
        """Execute the full retrieval pipeline.

        Returns:
            Tuple of (retrieved_document, structured_context).
        """
        retrieval_start = time.perf_counter()

        try:
            retrieved = self._retriever.search(
                query=query,
                patient_id=patient_id,
                report_id=report_id,
                document_type=document_type,
                top_k=top_k or self._config.top_k,
                min_score=min_score or self._config.min_score,
            )
        except Exception as exc:
            raise RetrievalError(f"Retrieval orchestration failed: {exc}") from exc

        retrieval_ms = (time.perf_counter() - retrieval_start) * 1000

        if not retrieved.results:
            return retrieved, RAGContext(
                context="",
                has_sufficient_context=False,
                build_time_ms=0.0,
            )

        context_start = time.perf_counter()

        try:
            result = self._context_builder.build(
                retrieved=retrieved,
                max_tokens=context_max_tokens or self._config.context_max_tokens,
                strategy=context_strategy or self._config.context_strategy,
            )
        except Exception as exc:
            raise ContextBuildError(f"Context building failed: {exc}") from exc

        context_ms = (time.perf_counter() - context_start) * 1000

        fragments_dicts = []
        citations_dicts = []
        for frag in result.fragments:
            fragments_dicts.append({
                "text": frag.text,
                "score": frag.score,
                "citation": frag.citation.model_dump(exclude_none=True) if frag.citation else {},
                "rank": frag.rank,
            })
        for cit in result.citations:
            citations_dicts.append(cit.model_dump(exclude_none=True))

        context = RAGContext(
            context=result.context,
            fragments=fragments_dicts,
            citations=citations_dicts,
            total_tokens=result.token_usage.estimated_tokens if result.token_usage else 0,
            fragment_count=len(result.fragments),
            has_sufficient_context=len(result.fragments) > 0,
            build_time_ms=round(context_ms, 2),
        )

        return retrieved, context

    @property
    def retriever(self) -> RetrieverService:
        return self._retriever

    @property
    def context_builder(self) -> ContextBuilder:
        return self._context_builder
