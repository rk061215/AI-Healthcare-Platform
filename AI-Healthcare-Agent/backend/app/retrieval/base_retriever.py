from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.retrieval.models import RetrievalMetrics, RetrievalQuery, RetrievalResult, RetrievedDocument


class BaseRetriever(ABC):
    """Abstract interface for all retriever providers."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the retriever and its underlying vector store connection."""

    @abstractmethod
    def retrieve(self, query: RetrievalQuery) -> RetrievedDocument:
        """Retrieve documents matching the query."""

    @abstractmethod
    def retrieve_by_patient(
        self,
        patient_id: str,
        query: Optional[str] = None,
        top_k: int = 20,
    ) -> RetrievedDocument:
        """Retrieve documents for a specific patient."""

    @abstractmethod
    def retrieve_by_report(
        self,
        report_id: str,
        query: Optional[str] = None,
        top_k: int = 50,
    ) -> RetrievedDocument:
        """Retrieve documents within a specific report."""

    @abstractmethod
    def retrieve_by_document_type(
        self,
        document_type: str,
        query: Optional[str] = None,
        top_k: int = 50,
    ) -> RetrievedDocument:
        """Retrieve documents of a specific type."""

    @abstractmethod
    def retrieve_with_scores(
        self,
        query: RetrievalQuery,
    ) -> RetrievedDocument:
        """Retrieve documents with raw similarity scores."""

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Verify the retriever is operational."""

    @abstractmethod
    def close(self) -> None:
        """Release retriever resources."""
