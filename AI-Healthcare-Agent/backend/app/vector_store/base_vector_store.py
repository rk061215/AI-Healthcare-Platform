from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.vector_store.models import CollectionInfo, IndexableDocument, SearchResult


class BaseVectorStore(ABC):
    """Abstract interface for all vector store providers.

    Every provider must implement all methods. No business logic should
    call a vector database directly — everything goes through this interface.
    """

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the vector store connection and create default collection."""

    @abstractmethod
    def add_documents(self, documents: list[IndexableDocument]) -> list[str]:
        """Index documents into the vector store.

        Returns the list of document IDs that were successfully added.
        """

    @abstractmethod
    def update_documents(self, documents: list[IndexableDocument]) -> None:
        """Update existing documents in the vector store.

        Documents are matched by ID. Metadata and embeddings are replaced.
        """

    @abstractmethod
    def delete_documents(self, ids: list[str]) -> None:
        """Delete documents by their IDs."""

    @abstractmethod
    def delete_collection(self, collection_name: str) -> None:
        """Delete an entire collection and all its documents."""

    @abstractmethod
    def similarity_search(
        self,
        query_vector: list[float],
        k: int = 10,
        filter: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        """Search for the k most similar vectors."""

    @abstractmethod
    def similarity_search_with_score(
        self,
        query_vector: list[float],
        k: int = 10,
        filter: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        """Search for the k most similar vectors with distance scores."""

    @abstractmethod
    def hybrid_search(
        self,
        query_vector: list[float],
        query_text: str,
        k: int = 10,
        filter: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        """Combined vector + keyword search.

        Default implementation delegates to similarity_search.
        Providers with native hybrid search should override this.
        """

    @abstractmethod
    def metadata_search(
        self,
        filter: dict[str, Any],
        k: int = 10,
    ) -> list[SearchResult]:
        """Search documents by metadata filter only (no vector similarity)."""

    @abstractmethod
    def list_collections(self) -> list[CollectionInfo]:
        """List all available collections."""

    @abstractmethod
    def create_collection(self, name: str) -> None:
        """Create a new collection."""

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Verify the vector store is operational.

        Returns a dict with at minimum:
            {"status": "ok" | "error", "error": str | None}
        """

    @abstractmethod
    def close(self) -> None:
        """Close the vector store connection and release resources."""
