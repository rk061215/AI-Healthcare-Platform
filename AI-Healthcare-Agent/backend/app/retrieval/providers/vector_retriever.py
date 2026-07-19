from __future__ import annotations

import time
from typing import Any, Optional

from app.retrieval.base_retriever import BaseRetriever
from app.retrieval.config import RetrieverConfig
from app.retrieval.exceptions import (
    ConfigurationError,
    HealthCheckFailedError,
    RetrieverNotInitializedError,
    SearchExecutionError,
)
from app.retrieval.models import (
    RetrievalMetrics,
    RetrievalQuery,
    RetrievalResult,
    RetrievedDocument,
)
from app.vector_store.config import VectorStoreConfig
from app.vector_store.models import SearchFilter, SearchResult
from app.vector_store.vector_service import VectorService

VECTOR_RETRIEVER_PROVIDER_NAME = "vector_retriever"


class VectorRetriever(BaseRetriever):
    """Retriever backed by the vector store (ChromaDB).

    Translates VectorService SearchResult into RetrievalResult models
    and provides the full BaseRetriever interface.
    """

    def __init__(
        self,
        config: Optional[RetrieverConfig] = None,
        vector_service: Optional[VectorService] = None,
    ) -> None:
        self._config = config or RetrieverConfig()
        self._vector_service = vector_service
        self._initialized = False

    def initialize(self) -> None:
        if self._vector_service is None:
            vs_config = VectorStoreConfig()
            self._vector_service = VectorService(config=vs_config)
        self._initialized = True

    def _check_initialized(self) -> None:
        if not self._initialized or self._vector_service is None:
            raise RetrieverNotInitializedError(
                "VectorRetriever is not initialized. Call initialize() first."
            )

    def _to_retrieval_result(self, sr: SearchResult) -> RetrievalResult:
        return RetrievalResult(
            chunk_id=sr.id,
            text=sr.text,
            score=sr.score,
            document_id=sr.metadata.get("document_id", sr.id),
            report_id=sr.report_id,
            patient_id=sr.patient_id,
            document_type=sr.document_type or "unknown",
            section=sr.section,
            page=sr.metadata.get("page"),
            chunk_index=sr.metadata.get("chunk_index", 0),
            source=sr.metadata.get("source", "ocr"),
            language=sr.metadata.get("language", "en"),
            embedding=sr.embedding,
            metadata=sr.metadata,
        )

    def _build_filter(
        self, query: RetrievalQuery
    ) -> Optional[dict[str, Any]]:
        parts: dict[str, Any] = {}
        if query.patient_id:
            parts["patient_id"] = query.patient_id
        if query.report_id:
            parts["report_id"] = query.report_id
        if query.document_type:
            parts["document_type"] = query.document_type
        if query.section:
            parts["section"] = query.section
        if query.source:
            parts["source"] = query.source
        if query.language:
            parts["language"] = query.language
        for k, v in query.metadata_filter.items():
            parts[k] = v
        return parts if parts else None

    def _filter_results(
        self, results: list[RetrievalResult], min_score: float
    ) -> list[RetrievalResult]:
        if min_score > 0.0:
            return [r for r in results if r.score >= min_score]
        return results

    def retrieve(self, query: RetrievalQuery) -> RetrievedDocument:
        self._check_initialized()
        start = time.perf_counter()

        try:
            filter_dict = self._build_filter(query)
            search_results = self._vector_service.search(
                query=query.text,
                k=query.top_k,
                filter=SearchFilter(**filter_dict) if filter_dict else None,
            )
        except Exception as exc:
            raise SearchExecutionError(f"Retrieval failed: {exc}") from exc

        raw_results = [self._to_retrieval_result(sr) for sr in search_results]
        filtered = self._filter_results(raw_results, query.min_score)

        elapsed = (time.perf_counter() - start) * 1000

        return RetrievedDocument(
            query=query,
            results=filtered[: query.top_k],
            total_results=len(raw_results),
            returned_results=min(len(filtered), query.top_k),
            retrieval_time_ms=round(elapsed, 2),
            provider=VECTOR_RETRIEVER_PROVIDER_NAME,
        )

    def retrieve_by_patient(
        self,
        patient_id: str,
        query: Optional[str] = None,
        top_k: int = 20,
    ) -> RetrievedDocument:
        self._check_initialized()
        start = time.perf_counter()

        try:
            search_results = self._vector_service.search_by_patient(
                patient_id=patient_id, query=query, k=top_k
            )
        except Exception as exc:
            raise SearchExecutionError(
                f"Patient retrieval failed: {exc}"
            ) from exc

        results = [self._to_retrieval_result(sr) for sr in search_results]
        elapsed = (time.perf_counter() - start) * 1000

        retrieval_query = RetrievalQuery(
            text=query or "",
            top_k=top_k,
            patient_id=patient_id,
        )

        return RetrievedDocument(
            query=retrieval_query,
            results=results[:top_k],
            total_results=len(results),
            returned_results=min(len(results), top_k),
            retrieval_time_ms=round(elapsed, 2),
            provider=VECTOR_RETRIEVER_PROVIDER_NAME,
        )

    def retrieve_by_report(
        self,
        report_id: str,
        query: Optional[str] = None,
        top_k: int = 50,
    ) -> RetrievedDocument:
        self._check_initialized()
        start = time.perf_counter()

        try:
            search_results = self._vector_service.search_by_report(
                report_id=report_id, query=query, k=top_k
            )
        except Exception as exc:
            raise SearchExecutionError(
                f"Report retrieval failed: {exc}"
            ) from exc

        results = [self._to_retrieval_result(sr) for sr in search_results]
        elapsed = (time.perf_counter() - start) * 1000

        retrieval_query = RetrievalQuery(
            text=query or "",
            top_k=top_k,
            report_id=report_id,
        )

        return RetrievedDocument(
            query=retrieval_query,
            results=results[:top_k],
            total_results=len(results),
            returned_results=min(len(results), top_k),
            retrieval_time_ms=round(elapsed, 2),
            provider=VECTOR_RETRIEVER_PROVIDER_NAME,
        )

    def retrieve_by_document_type(
        self,
        document_type: str,
        query: Optional[str] = None,
        top_k: int = 50,
    ) -> RetrievedDocument:
        self._check_initialized()
        start = time.perf_counter()

        try:
            search_results = self._vector_service.search_by_document_type(
                document_type=document_type, query=query, k=top_k
            )
        except Exception as exc:
            raise SearchExecutionError(
                f"Document type retrieval failed: {exc}"
            ) from exc

        results = [self._to_retrieval_result(sr) for sr in search_results]
        elapsed = (time.perf_counter() - start) * 1000

        retrieval_query = RetrievalQuery(
            text=query or "",
            top_k=top_k,
            document_type=document_type,
        )

        return RetrievedDocument(
            query=retrieval_query,
            results=results[:top_k],
            total_results=len(results),
            returned_results=min(len(results), top_k),
            retrieval_time_ms=round(elapsed, 2),
            provider=VECTOR_RETRIEVER_PROVIDER_NAME,
        )

    def retrieve_with_scores(
        self,
        query: RetrievalQuery,
    ) -> RetrievedDocument:
        return self.retrieve(query)

    def health_check(self) -> dict[str, Any]:
        if not self._initialized:
            return {"status": "error", "error": "Not initialized"}
        try:
            return self._vector_service.health_check()
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def close(self) -> None:
        self._initialized = False
        if self._vector_service:
            self._vector_service.close()
