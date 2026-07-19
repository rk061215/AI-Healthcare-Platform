from __future__ import annotations

import math
import re
import time
from typing import Any, Optional

from app.retrieval.base_retriever import BaseRetriever
from app.retrieval.config import RetrieverConfig
from app.retrieval.exceptions import HealthCheckFailedError, RetrieverNotInitializedError, SearchExecutionError
from app.retrieval.models import RetrievalMetrics, RetrievalQuery, RetrievalResult, RetrievedDocument
from app.vector_store.config import VectorStoreConfig
from app.vector_store.models import SearchFilter
from app.vector_store.vector_service import VectorService

KEYWORD_RETRIEVER_PROVIDER_NAME = "keyword_retriever"

STOP_WORDS: set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "need", "dare",
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves",
    "you", "your", "yours", "yourself", "he", "him", "his", "himself",
    "she", "her", "hers", "herself", "it", "its", "itself", "they",
    "them", "their", "theirs", "themselves", "what", "which", "who",
    "whom", "this", "that", "these", "those", "am", "about", "above",
    "after", "again", "against", "all", "any", "as", "at", "because",
    "before", "between", "both", "each", "few", "more", "most", "other",
    "some", "such", "no", "nor", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "also", "now", "here", "there",
}


class KeywordRetriever(BaseRetriever):
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
                "KeywordRetriever is not initialized. Call initialize() first."
            )

    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]

    def _score_by_keywords(
        self, text: str, query_terms: list[str], term_freqs: dict[str, int]
    ) -> float:
        text_lower = text.lower()
        score = 0.0
        text_len = len(text.split())

        for term in query_terms:
            if term in text_lower:
                count = text_lower.count(term)
                tf = count / max(text_len, 1)
                idf = math.log((1000 + 1) / (term_freqs.get(term, 1) + 1)) + 1
                score += tf * idf * (1.0 + math.log(1 + count))

        return score

    def _build_metadata_filter(
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

    def retrieve(self, query: RetrievalQuery) -> RetrievedDocument:
        self._check_initialized()
        start = time.perf_counter()

        try:
            query_terms = self._tokenize(query.text)
            if not query_terms:
                return RetrievedDocument(
                    query=query,
                    results=[],
                    total_results=0,
                    returned_results=0,
                    retrieval_time_ms=0.0,
                    provider=KEYWORD_RETRIEVER_PROVIDER_NAME,
                )

            filter_dict = self._build_metadata_filter(query)

            candidate_results = self._vector_service.store.similarity_search(
                [0.0] * 768,
                k=query.top_k * 3,
                filter=filter_dict,
            )
        except Exception as exc:
            raise SearchExecutionError(f"Keyword retrieval failed: {exc}") from exc

        term_freqs: dict[str, int] = {}
        for sr in candidate_results:
            for term in query_terms:
                if term in sr.text.lower():
                    term_freqs[term] = term_freqs.get(term, 0) + 1

        scored_results: list[tuple[float, RetrievalResult]] = []
        for sr in candidate_results:
            kw_score = self._score_by_keywords(sr.text, query_terms, term_freqs)
            if kw_score > 0:
                scored_results.append((
                    kw_score,
                    RetrievalResult(
                        chunk_id=sr.id,
                        text=sr.text,
                        score=kw_score,
                        document_id=sr.metadata.get("document_id", sr.id),
                        report_id=sr.report_id,
                        patient_id=sr.patient_id,
                        document_type=sr.document_type or "unknown",
                        section=sr.section,
                        page=sr.metadata.get("page"),
                        chunk_index=sr.metadata.get("chunk_index", 0),
                        source=sr.metadata.get("source", "ocr"),
                        language=sr.metadata.get("language", "en"),
                        metadata={**sr.metadata, "keyword_score": kw_score},
                    ),
                ))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        results = [r for _, r in scored_results[: query.top_k]]
        total = len(scored_results)

        elapsed = (time.perf_counter() - start) * 1000

        return RetrievedDocument(
            query=query,
            results=results,
            total_results=total,
            returned_results=len(results),
            retrieval_time_ms=round(elapsed, 2),
            provider=KEYWORD_RETRIEVER_PROVIDER_NAME,
        )

    def retrieve_by_patient(
        self, patient_id: str, query: Optional[str] = None, top_k: int = 20
    ) -> RetrievedDocument:
        self._check_initialized()
        rq = RetrievalQuery(
            text=query or "",
            top_k=top_k,
            patient_id=patient_id,
        )
        return self.retrieve(rq)

    def retrieve_by_report(
        self, report_id: str, query: Optional[str] = None, top_k: int = 50
    ) -> RetrievedDocument:
        self._check_initialized()
        rq = RetrievalQuery(
            text=query or "",
            top_k=top_k,
            report_id=report_id,
        )
        return self.retrieve(rq)

    def retrieve_by_document_type(
        self, document_type: str, query: Optional[str] = None, top_k: int = 50
    ) -> RetrievedDocument:
        self._check_initialized()
        rq = RetrievalQuery(
            text=query or "",
            top_k=top_k,
            document_type=document_type,
        )
        return self.retrieve(rq)

    def retrieve_with_scores(self, query: RetrievalQuery) -> RetrievedDocument:
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
