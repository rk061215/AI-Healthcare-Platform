from __future__ import annotations

import time
from typing import Any, Optional

from app.retrieval.base_retriever import BaseRetriever
from app.retrieval.config import RetrieverConfig
from app.retrieval.exceptions import QueryError, SearchExecutionError
from app.retrieval.models import RetrievalMetrics, RetrievalQuery, RetrievalResult, RetrievedDocument
from app.retrieval.retriever_factory import RetrieverFactory


class RetrieverService:
    """High-level retrieval operations.

    Coordinates between:
    - Query construction and validation
    - Retriever provider execution
    - Result normalization and metrics
    """

    def __init__(
        self,
        retriever: Optional[BaseRetriever] = None,
        config: Optional[RetrieverConfig] = None,
    ) -> None:
        self._config = config or RetrieverConfig()
        self._retriever = retriever or RetrieverFactory.create(config=self._config)

    @property
    def retriever(self) -> BaseRetriever:
        return self._retriever

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        patient_id: Optional[str] = None,
        report_id: Optional[str] = None,
        document_type: Optional[str] = None,
        section: Optional[str] = None,
        source: Optional[str] = None,
        min_score: float = 0.0,
    ) -> RetrievedDocument:
        """Execute a search with optional metadata filters."""
        if not query or not query.strip():
            raise QueryError("Search query cannot be empty")

        retrieval_query = RetrievalQuery(
            text=query.strip(),
            top_k=top_k or self._config.top_k,
            patient_id=patient_id,
            report_id=report_id,
            document_type=document_type,
            section=section,
            source=source,
            min_score=min_score,
        )
        return self._retriever.retrieve(retrieval_query)

    def search_by_patient(
        self,
        patient_id: str,
        query: Optional[str] = None,
        top_k: int = 20,
    ) -> RetrievedDocument:
        if not patient_id:
            raise QueryError("patient_id cannot be empty")
        return self._retriever.retrieve_by_patient(
            patient_id=patient_id, query=query, top_k=top_k
        )

    def search_by_report(
        self,
        report_id: str,
        query: Optional[str] = None,
        top_k: int = 50,
    ) -> RetrievedDocument:
        if not report_id:
            raise QueryError("report_id cannot be empty")
        return self._retriever.retrieve_by_report(
            report_id=report_id, query=query, top_k=top_k
        )

    def search_by_document_type(
        self,
        document_type: str,
        query: Optional[str] = None,
        top_k: int = 50,
    ) -> RetrievedDocument:
        if not document_type:
            raise QueryError("document_type cannot be empty")
        return self._retriever.retrieve_by_document_type(
            document_type=document_type, query=query, top_k=top_k
        )

    def health_check(self) -> dict[str, Any]:
        return self._retriever.health_check()

    def close(self) -> None:
        self._retriever.close()
