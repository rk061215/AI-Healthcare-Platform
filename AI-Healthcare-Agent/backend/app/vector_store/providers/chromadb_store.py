from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.vector_store.base_vector_store import BaseVectorStore
from app.vector_store.config import VectorStoreConfig
from app.vector_store.exceptions import (
    CollectionAlreadyExistsError,
    CollectionNotFoundError,
    DocumentOperationError,
    HealthCheckFailedError,
    SearchError,
)
from app.vector_store.models import CollectionInfo, IndexableDocument, SearchResult


CHROMADB_PROVIDER_NAME = "chromadb"

DISTANCE_FUNCTIONS = {
    "cosine": "cosine",
    "l2": "l2",
    "ip": "ip",
}


class ChromaDBStore(BaseVectorStore):
    """ChromaDB vector store implementation.

    Uses persistent local storage. No cloud dependencies.
    """

    def __init__(self, config: Optional[VectorStoreConfig] = None) -> None:
        self._config = config or VectorStoreConfig()
        self._client: Optional[chromadb.PersistentClient] = None
        self._collection: Optional[chromadb.Collection] = None
        self._initialized = False

    def initialize(self) -> None:
        persist_dir = self._config.persist_directory
        os.makedirs(persist_dir, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=False,
            ),
        )

        collection_name = self._config.collection_name
        existing = self._client.list_collections()
        existing_names = {c.name for c in existing}

        if collection_name in existing_names:
            self._collection = self._client.get_collection(name=collection_name)
        else:
            self._collection = self._client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": DISTANCE_FUNCTIONS.get(self._config.distance_function, "cosine")},
            )

        self._initialized = True

    def _check_initialized(self) -> None:
        if not self._initialized or self._collection is None:
            from app.vector_store.exceptions import ProviderNotInitializedError
            raise ProviderNotInitializedError(
                "ChromaDBStore is not initialized. Call initialize() first."
            )

    def add_documents(self, documents: list[IndexableDocument]) -> list[str]:
        self._check_initialized()
        if not documents:
            return []

        ids = []
        embeddings = []
        metadatas = []
        documents_text = []

        for doc in documents:
            ids.append(doc.id)
            embeddings.append(doc.embedding)
            metadatas.append(self._to_metadata(doc))
            documents_text.append(doc.text)

        try:
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents_text,
            )
            return ids
        except Exception as exc:
            raise DocumentOperationError(f"Failed to add documents: {exc}") from exc

    def update_documents(self, documents: list[IndexableDocument]) -> None:
        self._check_initialized()
        if not documents:
            return

        ids = []
        embeddings = []
        metadatas = []
        documents_text = []

        for doc in documents:
            ids.append(doc.id)
            embeddings.append(doc.embedding)
            metadatas.append(self._to_metadata(doc))
            documents_text.append(doc.text)

        try:
            self._collection.update(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents_text,
            )
        except Exception as exc:
            raise DocumentOperationError(f"Failed to update documents: {exc}") from exc

    def delete_documents(self, ids: list[str]) -> None:
        self._check_initialized()
        if not ids:
            return
        try:
            self._collection.delete(ids=ids)
        except Exception as exc:
            raise DocumentOperationError(f"Failed to delete documents: {exc}") from exc

    def delete_collection(self, collection_name: str) -> None:
        self._check_initialized()
        try:
            self._client.delete_collection(name=collection_name)
        except ValueError as exc:
            raise CollectionNotFoundError(f"Collection '{collection_name}' not found: {exc}") from exc
        except Exception as exc:
            raise DocumentOperationError(f"Failed to delete collection: {exc}") from exc

    def similarity_search(
        self,
        query_vector: list[float],
        k: int = 10,
        filter: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        return self._search(query_vector=query_vector, k=k, filter=filter)

    def similarity_search_with_score(
        self,
        query_vector: list[float],
        k: int = 10,
        filter: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        return self._search(query_vector=query_vector, k=k, filter=filter, include_distances=True)

    def hybrid_search(
        self,
        query_vector: list[float],
        query_text: str,
        k: int = 10,
        filter: Optional[dict[str, Any]] = None,
    ) -> list[SearchResult]:
        return self._search(query_vector=query_vector, k=k, filter=filter)

    def metadata_search(
        self,
        filter: dict[str, Any],
        k: int = 10,
    ) -> list[SearchResult]:
        self._check_initialized()
        dummy_vector = self._get_dummy_vector()
        try:
            results = self._collection.query(
                query_embeddings=[dummy_vector],
                n_results=k,
                where=filter if filter else None,
                include=["metadatas", "documents", "distances"],
            )
        except Exception as exc:
            raise SearchError(f"Metadata search failed: {exc}") from exc

        return self._results_to_list(results)

    def list_collections(self) -> list[CollectionInfo]:
        self._check_initialized()
        collections = self._client.list_collections()
        result = []
        for c in collections:
            try:
                count = c.count()
            except Exception:
                count = 0
            result.append(
                CollectionInfo(
                    name=c.name,
                    dimension=0,
                    count=count,
                    distance_function=self._config.distance_function,
                    metadata=c.metadata or {},
                )
            )
        return result

    def create_collection(self, name: str) -> None:
        self._check_initialized()
        existing = {c.name for c in self._client.list_collections()}
        if name in existing:
            raise CollectionAlreadyExistsError(f"Collection '{name}' already exists")
        self._client.create_collection(
            name=name,
            metadata={"hnsw:space": DISTANCE_FUNCTIONS.get(self._config.distance_function, "cosine")},
        )

    def health_check(self) -> dict[str, Any]:
        try:
            if not self._initialized or self._client is None:
                return {"status": "error", "error": "Not initialized"}
            self._client.heartbeat()
            count = self._collection.count() if self._collection else 0
            return {
                "status": "ok",
                "provider": CHROMADB_PROVIDER_NAME,
                "collection": self._config.collection_name,
                "document_count": count,
                "distance_function": self._config.distance_function,
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def close(self) -> None:
        self._initialized = False
        self._collection = None
        self._client = None

    # -- Private helpers --

    def _search(
        self,
        query_vector: list[float],
        k: int = 10,
        filter: Optional[dict[str, Any]] = None,
        include_distances: bool = False,
    ) -> list[SearchResult]:
        self._check_initialized()
        try:
            results = self._collection.query(
                query_embeddings=[query_vector],
                n_results=k,
                where=filter if filter else None,
                include=["metadatas", "documents", "distances"],
            )
        except Exception as exc:
            raise SearchError(f"Similarity search failed: {exc}") from exc

        return self._results_to_list(results)

    def _get_dummy_vector(self) -> list[float]:
        try:
            sample = self._collection.get(limit=1)
            if sample and sample.get("embeddings") and len(sample["embeddings"]) > 0:
                return [0.0] * len(sample["embeddings"][0])
        except Exception:
            pass
        return [0.0, 0.0, 0.0]

    def _results_to_list(self, results: dict) -> list[SearchResult]:
        output: list[SearchResult] = []
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]

        for i in range(len(ids)):
            score = 1.0 - distances[i] if distances and i < len(distances) else 0.0
            output.append(
                SearchResult(
                    id=ids[i],
                    text=documents[i] if documents and i < len(documents) else "",
                    score=round(score, 6),
                    metadata=metadatas[i] if metadatas and i < len(metadatas) else {},
                )
            )
        return output

    def _to_metadata(self, doc: IndexableDocument) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "document_type": doc.document_type,
            "chunk_index": doc.chunk_index,
            "document_version": doc.document_version,
            "schema_version": doc.schema_version,
            "embedding_version": doc.embedding_version,
            "source": doc.source,
            "language": doc.language,
            "provider": doc.provider,
        }
        if doc.patient_id:
            meta["patient_id"] = doc.patient_id
        if doc.report_id:
            meta["report_id"] = doc.report_id
        if doc.section:
            meta["section"] = doc.section
        if doc.page is not None:
            meta["page"] = doc.page
        if doc.extra:
            for k, v in doc.extra.items():
                meta[f"extra_{k}"] = v
        return meta
