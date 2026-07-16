from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from app.document_pipeline.chunk import DocumentChunk
from app.embeddings.embedding_service import EmbeddingService
from app.vector_store.base_vector_store import BaseVectorStore
from app.vector_store.config import VectorStoreConfig
from app.vector_store.exceptions import DocumentOperationError, SearchError
from app.vector_store.models import (
    CollectionInfo,
    IndexableDocument,
    SearchFilter,
    SearchResult,
)
from app.vector_store.vector_store_factory import VectorStoreFactory


class VectorService:
    """High-level vector store operations.

    Coordinates between:
    - Document Pipeline (DocumentChunk → IndexableDocument)
    - Embedding Service (text → embedding vector)
    - Vector Store (index, search, delete)
    """

    def __init__(
        self,
        store: Optional[BaseVectorStore] = None,
        embedding_service: Optional[EmbeddingService] = None,
        config: Optional[VectorStoreConfig] = None,
    ) -> None:
        self._config = config or VectorStoreConfig()
        self._store = store or VectorStoreFactory.create(config=self._config)
        self._embedding_service = embedding_service or EmbeddingService()

    @property
    def store(self) -> BaseVectorStore:
        return self._store

    @property
    def embedding_service(self) -> EmbeddingService:
        return self._embedding_service

    # -- Indexing --

    def index_chunks(
        self,
        chunks: list[DocumentChunk],
    ) -> list[str]:
        """Index document pipeline chunks into the vector store.

        Each chunk is embedded using the configured embedding service,
        then stored with full metadata.
        """
        if not chunks:
            return []

        texts = [c.text for c in chunks]
        try:
            vectors, metas = self._embedding_service.embed_batch(texts)
        except Exception as exc:
            raise DocumentOperationError(f"Failed to embed chunks: {exc}") from exc

        documents = []
        for i, chunk in enumerate(chunks):
            doc = IndexableDocument(
                id=chunk.chunk_id or f"chunk_{chunk.metadata.chunk_index}",
                text=chunk.text,
                embedding=vectors[i],
                document_type=chunk.metadata.document_type,
                patient_id=chunk.metadata.patient_id,
                report_id=chunk.metadata.report_id,
                section=chunk.metadata.section,
                page=chunk.metadata.page,
                chunk_index=chunk.metadata.chunk_index,
                document_version=chunk.metadata.chunk_version,
                schema_version=chunk.metadata.schema_version,
                embedding_version=chunk.metadata.embedding_version or metas[i].embedding_version,
                source=chunk.metadata.source,
                language=chunk.metadata.language,
                provider=chunk.metadata.provider,
                created_at=datetime.utcnow(),
            )
            documents.append(doc)

        return self._store.add_documents(documents)

    def index_text(
        self,
        text: str,
        doc_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Index a single text string with optional metadata."""
        vector, meta = self._embedding_service.embed(text)
        doc = IndexableDocument(
            id=doc_id or f"doc_{datetime.utcnow().timestamp()}",
            text=text,
            embedding=vector,
            embedding_version=str(meta.embedding_version),
            **(metadata or {}),
        )
        ids = self._store.add_documents([doc])
        return ids[0] if ids else ""

    # -- Search --

    def search(
        self,
        query: str,
        k: int = 10,
        filter: Optional[SearchFilter] = None,
    ) -> list[SearchResult]:
        """Search by text query with optional metadata filter."""
        try:
            query_vector, _ = self._embedding_service.embed_query(query)
        except Exception as exc:
            raise SearchError(f"Failed to embed query: {exc}") from exc

        filter_dict = filter.to_chroma_filter() if filter else None
        return self._store.similarity_search(query_vector, k=k, filter=filter_dict)

    def search_by_vector(
        self,
        query_vector: list[float],
        k: int = 10,
        filter: Optional[SearchFilter] = None,
    ) -> list[SearchResult]:
        """Search by raw embedding vector."""
        filter_dict = filter.to_chroma_filter() if filter else None
        return self._store.similarity_search(query_vector, k=k, filter=filter_dict)

    def search_by_patient(
        self,
        patient_id: str,
        query: Optional[str] = None,
        k: int = 20,
    ) -> list[SearchResult]:
        """Search within a specific patient's documents."""
        filter_obj = SearchFilter(patient_id=patient_id)
        if query:
            return self.search(query, k=k, filter=filter_obj)
        return self._store.metadata_search(filter=filter_obj.to_chroma_filter(), k=k)

    def search_by_report(
        self,
        report_id: str,
        query: Optional[str] = None,
        k: int = 50,
    ) -> list[SearchResult]:
        """Search within a specific report."""
        filter_obj = SearchFilter(report_id=report_id)
        if query:
            return self.search(query, k=k, filter=filter_obj)
        return self._store.metadata_search(filter=filter_obj.to_chroma_filter(), k=k)

    def search_by_document_type(
        self,
        document_type: str,
        query: Optional[str] = None,
        k: int = 50,
    ) -> list[SearchResult]:
        """Search within a specific document type."""
        filter_obj = SearchFilter(document_type=document_type)
        if query:
            return self.search(query, k=k, filter=filter_obj)
        return self._store.metadata_search(filter=filter_obj.to_chroma_filter(), k=k)

    # -- Management --

    def delete(self, ids: list[str]) -> None:
        """Delete documents by their IDs."""
        self._store.delete_documents(ids)

    def list_collections(self) -> list[CollectionInfo]:
        """List all available collections."""
        return self._store.list_collections()

    def health_check(self) -> dict[str, Any]:
        """Check vector store and embedding service health."""
        store_health = self._store.health_check()
        embed_health = self._embedding_service.health_check()
        return {
            "vector_store": store_health,
            "embedding_service": embed_health,
        }

    def close(self) -> None:
        """Release resources."""
        self._store.close()
