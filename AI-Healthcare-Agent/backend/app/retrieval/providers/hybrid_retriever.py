from __future__ import annotations

import time
from typing import Any, Optional

from app.retrieval.base_retriever import BaseRetriever
from app.retrieval.config import RetrieverConfig
from app.retrieval.exceptions import RetrieverNotInitializedError, SearchExecutionError
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.models import RetrievalMetrics, RetrievalQuery, RetrievalResult, RetrievedDocument
from app.retrieval.providers.keyword_retriever import KEYWORD_RETRIEVER_PROVIDER_NAME, KeywordRetriever
from app.retrieval.providers.vector_retriever import VECTOR_RETRIEVER_PROVIDER_NAME, VectorRetriever

HYBRID_RETRIEVER_PROVIDER_NAME = "hybrid_retriever"


class HybridRetriever(BaseRetriever):
    def __init__(
        self,
        config: Optional[RetrieverConfig] = None,
        vector_retriever: Optional[VectorRetriever] = None,
        keyword_retriever: Optional[KeywordRetriever] = None,
    ) -> None:
        self._config = config or RetrieverConfig()
        self._vector_retriever = vector_retriever or VectorRetriever(config=config)
        self._keyword_retriever = keyword_retriever or KeywordRetriever(config=config)
        self._initialized = False

    def initialize(self) -> None:
        self._vector_retriever.initialize()
        self._keyword_retriever.initialize()
        self._initialized = True

    def _check_initialized(self) -> None:
        if not self._initialized:
            raise RetrieverNotInitializedError(
                "HybridRetriever is not initialized. Call initialize() first."
            )

    def _hybrid_retrieve(
        self, query: RetrievalQuery, vector_k_multiplier: int = 3, keyword_k_multiplier: int = 3
    ) -> RetrievedDocument:
        self._check_initialized()

        start = time.perf_counter()

        vector_query = RetrievalQuery(
            text=query.text,
            top_k=query.top_k * vector_k_multiplier,
            patient_id=query.patient_id,
            report_id=query.report_id,
            document_type=query.document_type,
            section=query.section,
            source=query.source,
            language=query.language,
            metadata_filter=query.metadata_filter,
            min_score=query.min_score,
        )

        keyword_query = RetrievalQuery(
            text=query.text,
            top_k=query.top_k * keyword_k_multiplier,
            patient_id=query.patient_id,
            report_id=query.report_id,
            document_type=query.document_type,
            section=query.section,
            source=query.source,
            language=query.language,
            metadata_filter=query.metadata_filter,
            min_score=0.0,
        )

        try:
            vector_result = self._vector_retriever.retrieve(vector_query)
            keyword_result = self._keyword_retriever.retrieve(keyword_query)
        except Exception as exc:
            raise SearchExecutionError(f"Hybrid retrieval failed: {exc}") from exc

        fused = reciprocal_rank_fusion(
            [vector_result.results, keyword_result.results],
            top_n=query.top_k,
        )

        elapsed = (time.perf_counter() - start) * 1000

        return RetrievedDocument(
            query=query,
            results=fused,
            total_results=vector_result.total_results + keyword_result.total_results,
            returned_results=len(fused),
            retrieval_time_ms=round(elapsed, 2),
            provider=HYBRID_RETRIEVER_PROVIDER_NAME,
        )

    def retrieve(self, query: RetrievalQuery) -> RetrievedDocument:
        return self._hybrid_retrieve(query)

    def retrieve_by_patient(
        self, patient_id: str, query: Optional[str] = None, top_k: int = 20
    ) -> RetrievedDocument:
        self._check_initialized()
        rq = RetrievalQuery(
            text=query or "",
            top_k=top_k,
            patient_id=patient_id,
        )
        return self._hybrid_retrieve(rq)

    def retrieve_by_report(
        self, report_id: str, query: Optional[str] = None, top_k: int = 50
    ) -> RetrievedDocument:
        self._check_initialized()
        rq = RetrievalQuery(
            text=query or "",
            top_k=top_k,
            report_id=report_id,
        )
        return self._hybrid_retrieve(rq)

    def retrieve_by_document_type(
        self, document_type: str, query: Optional[str] = None, top_k: int = 50
    ) -> RetrievedDocument:
        self._check_initialized()
        rq = RetrievalQuery(
            text=query or "",
            top_k=top_k,
            document_type=document_type,
        )
        return self._hybrid_retrieve(rq)

    def retrieve_with_scores(self, query: RetrievalQuery) -> RetrievedDocument:
        return self._hybrid_retrieve(query)
    
    def health_check(self) -> dict[str, Any]:
        if not self._initialized:
            return {"status": "error", "error": "Not initialized"}
        vector_health = self._vector_retriever.health_check()
        keyword_health = self._keyword_retriever.health_check()
        return {
            "status": "ok" if vector_health.get("status") == "ok" else "degraded",
            "vector": vector_health,
            "keyword": keyword_health,
        }

    def close(self) -> None:
        self._initialized = False
        self._vector_retriever.close()
        self._keyword_retriever.close()
