from __future__ import annotations

from typing import Any, Optional

from app.retrieval.base_retriever import BaseRetriever
from app.retrieval.config import RetrieverConfig
from app.retrieval.models import RetrievalQuery, RetrievalResult, RetrievedDocument


HYBRID_RETRIEVER_PROVIDER_NAME = "hybrid_retriever"


class HybridRetriever(BaseRetriever):
    """Hybrid vector + keyword retriever (future implementation)."""

    def __init__(self, config: Optional[RetrieverConfig] = None) -> None:
        self._config = config or RetrieverConfig()

    def initialize(self) -> None:
        raise NotImplementedError("HybridRetriever is not yet implemented")

    def retrieve(self, query: RetrievalQuery) -> RetrievedDocument:
        raise NotImplementedError("HybridRetriever is not yet implemented")

    def retrieve_by_patient(
        self, patient_id: str, query: Optional[str] = None, top_k: int = 20
    ) -> RetrievedDocument:
        raise NotImplementedError("HybridRetriever is not yet implemented")

    def retrieve_by_report(
        self, report_id: str, query: Optional[str] = None, top_k: int = 50
    ) -> RetrievedDocument:
        raise NotImplementedError("HybridRetriever is not yet implemented")

    def retrieve_by_document_type(
        self, document_type: str, query: Optional[str] = None, top_k: int = 50
    ) -> RetrievedDocument:
        raise NotImplementedError("HybridRetriever is not yet implemented")

    def retrieve_with_scores(self, query: RetrievalQuery) -> RetrievedDocument:
        raise NotImplementedError("HybridRetriever is not yet implemented")

    def health_check(self) -> dict[str, Any]:
        return {"status": "error", "error": "Not implemented"}

    def close(self) -> None:
        pass
