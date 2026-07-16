from __future__ import annotations

import os
import tempfile
from datetime import datetime
from typing import Any

import pytest

from app.document_pipeline.chunk import ChunkMetadata, DocumentChunk
from app.vector_store import (
    CHROMADB_PROVIDER_NAME,
    PINECONE_PROVIDER_NAME,
    QDRANT_PROVIDER_NAME,
    WEAVIATE_PROVIDER_NAME,
    BaseVectorStore,
    CollectionAlreadyExistsError,
    CollectionNotFoundError,
    ConfigurationError,
    DocumentOperationError,
    HealthCheckFailedError,
    ProviderNotInitializedError,
    ProviderNotFoundError,
    SearchError,
    CollectionInfo,
    IndexableDocument,
    SearchFilter,
    SearchResult,
    VectorStoreConfig,
    VectorStoreFactory,
    VectorStoreRegistry,
    VectorService,
)
from app.vector_store.exceptions import VectorStoreError
from app.vector_store.providers import ChromaDBStore
import app.vector_store.providers.chromadb_store  # noqa: F401
import app.vector_store.providers.future.qdrant_store  # noqa: F401
import app.vector_store.providers.future.weaviate_store  # noqa: F401
import app.vector_store.providers.future.pinecone_store  # noqa: F401

# =============================================================================
# Test helpers
# =============================================================================


def _save_registry() -> dict[str, type[BaseVectorStore]]:
    return VectorStoreRegistry._save_registry()


def _restore_registry(saved: dict[str, type[BaseVectorStore]]) -> None:
    VectorStoreRegistry._restore_registry(saved)


@pytest.fixture(autouse=True)
def registry_isolation():
    saved = _save_registry()
    yield
    VectorStoreRegistry.clear()
    _restore_registry(saved)


# =============================================================================
# Mock store for testing the abstract layer
# =============================================================================


class MockVectorStore(BaseVectorStore):
    """In-memory mock for testing BaseVectorStore interface consumers."""

    def __init__(self, config=None):
        self._config = config or VectorStoreConfig()
        self._docs: dict[str, IndexableDocument] = {}
        self._initialized = False
        self._fail = False

    def initialize(self) -> None:
        self._initialized = True

    def add_documents(self, documents: list[IndexableDocument]) -> list[str]:
        if self._fail:
            raise DocumentOperationError("Mock add failure")
        ids = []
        for doc in documents:
            self._docs[doc.id] = doc
            ids.append(doc.id)
        return ids

    def update_documents(self, documents: list[IndexableDocument]) -> None:
        if self._fail:
            raise DocumentOperationError("Mock update failure")
        for doc in documents:
            self._docs[doc.id] = doc

    def delete_documents(self, ids: list[str]) -> None:
        if self._fail:
            raise DocumentOperationError("Mock delete failure")
        for i in ids:
            self._docs.pop(i, None)

    def delete_collection(self, collection_name: str) -> None:
        if self._fail:
            raise DocumentOperationError("Mock delete failure")
        self._docs.clear()

    def similarity_search(
        self,
        query_vector: list[float],
        k: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        if self._fail:
            raise SearchError("Mock search failure")
        results = []
        for doc in list(self._docs.values())[:k]:
            results.append(
                SearchResult(id=doc.id, text=doc.text, score=0.95, metadata={})
            )
        return results

    def similarity_search_with_score(
        self,
        query_vector: list[float],
        k: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        return self.similarity_search(query_vector, k, filter)

    def hybrid_search(
        self,
        query_vector: list[float],
        query_text: str,
        k: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        return self.similarity_search(query_vector, k, filter)

    def metadata_search(
        self,
        filter: dict[str, Any],
        k: int = 10,
    ) -> list[SearchResult]:
        return self.similarity_search([0.0], k, filter)

    def list_collections(self) -> list[CollectionInfo]:
        return [
            CollectionInfo(
                name="test_collection",
                dimension=3,
                count=len(self._docs),
                distance_function="cosine",
            )
        ]

    def create_collection(self, name: str) -> None:
        pass

    def health_check(self) -> dict[str, Any]:
        if not self._initialized:
            return {"status": "error", "error": "Not initialized"}
        return {
            "status": "ok",
            "provider": "mock",
            "collection": "test",
            "document_count": len(self._docs),
        }

    def close(self) -> None:
        self._initialized = False


VectorStoreRegistry.register("mock", MockVectorStore)


# =============================================================================
# Mock embedding service for VectorService tests
# =============================================================================


class MockEmbeddingService:
    """Minimal mock that avoids importing the real embedding layer."""

    def embed(self, text: str) -> tuple[list[float], Any]:
        return [0.1, 0.2, 0.3], type("Meta", (), {"embedding_version": "1.0"})()

    def embed_batch(self, texts: list[str]) -> tuple[list[list[float]], list[Any]]:
        vectors = [[0.1, 0.2, 0.3]] * len(texts)
        metas = [type("Meta", (), {"embedding_version": "1.0"})() for _ in texts]
        return vectors, metas

    def embed_query(self, text: str) -> tuple[list[float], Any]:
        return self.embed(text)

    def health_check(self) -> dict[str, Any]:
        return {"status": "ok", "provider": "mock"}


# =============================================================================
# IndexableDocument / SearchResult Tests
# =============================================================================


class TestIndexableDocument:
    def test_defaults(self):
        doc = IndexableDocument(
            id="doc1",
            text="hello",
            embedding=[0.1, 0.2, 0.3],
        )
        assert doc.id == "doc1"
        assert doc.text == "hello"
        assert doc.embedding == [0.1, 0.2, 0.3]
        assert doc.document_type == "unknown"
        assert doc.patient_id is None
        assert doc.report_id is None
        assert doc.chunk_index == 0
        assert doc.document_version == "1.0.0"
        assert doc.source == "ocr"
        assert doc.language == "en"
        assert doc.provider == "unknown"
        assert isinstance(doc.created_at, datetime)
        assert doc.extra == {}

    def test_with_all_fields(self):
        doc = IndexableDocument(
            id="doc2",
            text="patient data",
            embedding=[0.5, 0.6],
            document_type="lab_report",
            patient_id="P001",
            report_id="R001",
            section="results",
            page=3,
            chunk_index=1,
            document_version="2.0.0",
            schema_version="2.0.0",
            embedding_version="gemini-v2",
            source="upload",
            language="fr",
            provider="gemini",
            extra={"key": "val"},
        )
        assert doc.document_type == "lab_report"
        assert doc.patient_id == "P001"
        assert doc.report_id == "R001"
        assert doc.section == "results"
        assert doc.page == 3
        assert doc.extra["key"] == "val"

    def test_forbids_extra_fields(self):
        with pytest.raises(Exception):
            IndexableDocument(
                id="bad",
                text="x",
                embedding=[0.0],
                unknown_field="value",
            )


class TestSearchResult:
    def test_properties(self):
        result = SearchResult(
            id="r1",
            text="result text",
            score=0.95,
            metadata={"patient_id": "P001", "report_id": "R001", "document_type": "note", "section": "history"},
        )
        assert result.patient_id == "P001"
        assert result.report_id == "R001"
        assert result.document_type == "note"
        assert result.section == "history"

    def test_missing_metadata(self):
        result = SearchResult(id="r2", text="no meta", score=0.5)
        assert result.patient_id is None
        assert result.report_id is None
        assert result.document_type is None
        assert result.section is None

    def test_extra_forbidden(self):
        with pytest.raises(Exception):
            SearchResult(id="bad", text="x", score=0.0, wrong=True)  # type: ignore


class TestCollectionInfo:
    def test_defaults(self):
        info = CollectionInfo(name="col1", dimension=128, count=100)
        assert info.name == "col1"
        assert info.dimension == 128
        assert info.count == 100
        assert info.distance_function == "cosine"
        assert info.metadata == {}


class TestSearchFilter:
    def test_empty(self):
        f = SearchFilter()
        assert f.to_chroma_filter() == {}

    def test_all_fields(self):
        f = SearchFilter(
            patient_id="P001",
            report_id="R002",
            document_type="lab_report",
            section="results",
            source="ocr",
            language="en",
            metadata={"extra_key": "extra_val"},
        )
        result = f.to_chroma_filter()
        assert result["patient_id"] == "P001"
        assert result["report_id"] == "R002"
        assert result["document_type"] == "lab_report"
        assert result["section"] == "results"
        assert result["source"] == "ocr"
        assert result["language"] == "en"
        assert result["extra_key"] == "extra_val"

    def test_partial_fields(self):
        f = SearchFilter(patient_id="P003", document_type="note")
        result = f.to_chroma_filter()
        assert result == {"patient_id": "P003", "document_type": "note"}

    def test_extra_forbidden(self):
        with pytest.raises(Exception):
            SearchFilter(unknown=True)  # type: ignore


# =============================================================================
# VectorStoreConfig Tests
# =============================================================================


class TestVectorStoreConfig:
    def test_default_provider(self):
        cfg = VectorStoreConfig()
        assert cfg.provider == "chromadb"

    def test_custom_provider(self):
        cfg = VectorStoreConfig(provider="qdrant")
        assert cfg.provider == "qdrant"

    def test_default_collection(self):
        cfg = VectorStoreConfig()
        assert cfg.collection_name == "document_chunks"

    def test_custom_collection(self):
        cfg = VectorStoreConfig(collection_name="custom_collection")
        assert cfg.collection_name == "custom_collection"

    def test_default_distance_function(self):
        cfg = VectorStoreConfig()
        assert cfg.distance_function == "cosine"

    def test_default_path(self):
        cfg = VectorStoreConfig()
        assert cfg.persist_directory == "./chromadb_data"

    def test_default_batch_size(self):
        cfg = VectorStoreConfig()
        assert cfg.batch_size == 100


# =============================================================================
# VectorStoreRegistry Tests
# =============================================================================


class TestVectorStoreRegistry:
    def test_register_and_get(self):
        VectorStoreRegistry.register("test_provider", MockVectorStore)
        cls = VectorStoreRegistry.get("test_provider")
        assert cls is MockVectorStore

    def test_get_unregistered(self):
        with pytest.raises(ProviderNotFoundError, match="not registered"):
            VectorStoreRegistry.get("nonexistent")

    def test_list_providers(self):
        providers = VectorStoreRegistry.list_providers()
        assert "mock" in providers

    def test_register_overwrite(self):
        VectorStoreRegistry.register("dup", MockVectorStore)

        class OtherMock(MockVectorStore):
            pass

        VectorStoreRegistry.register("dup", OtherMock)
        assert VectorStoreRegistry.get("dup") is OtherMock

    def test_clear(self):
        VectorStoreRegistry.clear()
        assert VectorStoreRegistry.list_providers() == []

    def test_save_and_restore(self):
        saved = _save_registry()
        VectorStoreRegistry.clear()
        VectorStoreRegistry.register("new", MockVectorStore)
        _restore_registry(saved)
        assert "mock" in VectorStoreRegistry.list_providers()
        assert "new" not in VectorStoreRegistry.list_providers()


# =============================================================================
# VectorStoreFactory Tests
# =============================================================================


class TestVectorStoreFactory:
    def test_create_mock(self):
        config = VectorStoreConfig(provider="mock")
        store = VectorStoreFactory.create(config)
        assert isinstance(store, MockVectorStore)
        assert store._initialized

    def test_default_config(self):
        saved = _save_registry()
        VectorStoreRegistry.clear()
        VectorStoreRegistry.register("chromadb", MockVectorStore)
        store = VectorStoreFactory.create()
        assert isinstance(store, MockVectorStore)
        _restore_registry(saved)

    def test_unknown_provider(self):
        config = VectorStoreConfig(provider="unknown_provider")
        with pytest.raises(ProviderNotFoundError):
            VectorStoreFactory.create(config)


# =============================================================================
# MockVectorStore (BaseVectorStore interface) Tests
# =============================================================================


class TestMockVectorStore:
    def test_add_and_search(self):
        store = MockVectorStore()
        store.initialize()
        doc = IndexableDocument(id="d1", text="test", embedding=[0.1, 0.2, 0.3])
        store.add_documents([doc])
        results = store.similarity_search([0.1, 0.2, 0.3], k=5)
        assert len(results) == 1
        assert results[0].id == "d1"

    def test_update(self):
        store = MockVectorStore()
        store.initialize()
        doc = IndexableDocument(id="d1", text="original", embedding=[0.1, 0.2, 0.3])
        store.add_documents([doc])
        updated = IndexableDocument(id="d1", text="updated", embedding=[0.4, 0.5, 0.6])
        store.update_documents([updated])
        results = store.similarity_search([0.4, 0.5, 0.6], k=5)
        assert results[0].text == "updated"

    def test_delete(self):
        store = MockVectorStore()
        store.initialize()
        store.add_documents([IndexableDocument(id="d1", text="x", embedding=[0.1])])
        store.add_documents([IndexableDocument(id="d2", text="y", embedding=[0.2])])
        store.delete_documents(["d1"])
        results = store.similarity_search([0.0], k=5)
        assert len(results) == 1
        assert results[0].id == "d2"

    def test_delete_collection(self):
        store = MockVectorStore()
        store.initialize()
        store.add_documents([IndexableDocument(id="d1", text="x", embedding=[0.1])])
        store.delete_collection("test")
        results = store.similarity_search([0.0], k=5)
        assert len(results) == 0

    def test_health_check(self):
        store = MockVectorStore()
        health = store.health_check()
        assert health["status"] == "error"
        store.initialize()
        health = store.health_check()
        assert health["status"] == "ok"

    def test_close(self):
        store = MockVectorStore()
        store.initialize()
        store.close()
        assert not store._initialized

    def test_empty_add_returns_empty(self):
        store = MockVectorStore()
        store.initialize()
        ids = store.add_documents([])
        assert ids == []

    def test_empty_update_no_error(self):
        store = MockVectorStore()
        store.initialize()
        store.update_documents([])

    def test_empty_delete_no_error(self):
        store = MockVectorStore()
        store.initialize()
        store.delete_documents([])

    def test_metadata_search(self):
        store = MockVectorStore()
        store.initialize()
        store.add_documents([IndexableDocument(id="m1", text="meta", embedding=[0.1])])
        results = store.metadata_search({"patient_id": "P001"}, k=5)
        assert len(results) == 1

    def test_similarity_search_with_score(self):
        store = MockVectorStore()
        store.initialize()
        store.add_documents([IndexableDocument(id="s1", text="score", embedding=[0.1])])
        results = store.similarity_search_with_score([0.1], k=5)
        assert len(results) == 1

    def test_hybrid_search(self):
        store = MockVectorStore()
        store.initialize()
        store.add_documents([IndexableDocument(id="h1", text="hybrid", embedding=[0.1])])
        results = store.hybrid_search([0.1], "hybrid", k=5)
        assert len(results) == 1

    def test_list_collections(self):
        store = MockVectorStore()
        store.initialize()
        collections = store.list_collections()
        assert len(collections) == 1
        assert collections[0].name == "test_collection"

    def test_create_collection(self):
        store = MockVectorStore()
        store.initialize()
        store.create_collection("new_collection")


# =============================================================================
# ChromaDBStore Tests
# =============================================================================


@pytest.fixture
def chromadb_config():
    tmpdir = tempfile.mkdtemp(prefix="chroma_test_")
    yield VectorStoreConfig(
        provider="chromadb",
        collection_name="test_collection",
        persist_directory=tmpdir,
    )
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def chromadb_store(chromadb_config):
    store = ChromaDBStore(config=chromadb_config)
    store.initialize()
    yield store
    try:
        store.close()
    except Exception:
        pass


class TestChromaDBStore:
    def test_initialize_creates_collection(self, chromadb_config):
        store = ChromaDBStore(config=chromadb_config)
        store.initialize()
        assert store._initialized
        collections = store.list_collections()
        names = [c.name for c in collections]
        assert chromadb_config.collection_name in names
        store.close()

    def test_double_initialize(self, chromadb_config):
        store = ChromaDBStore(config=chromadb_config)
        store.initialize()
        store.initialize()
        assert store._initialized
        store.close()

    def test_add_and_search(self, chromadb_store):
        doc = IndexableDocument(
            id="test_add_1",
            text="Patient has high blood pressure",
            embedding=[0.1] * 3,
            patient_id="P001",
            document_type="lab_report",
        )
        chromadb_store.add_documents([doc])
        results = chromadb_store.similarity_search([0.1] * 3, k=5)
        assert len(results) >= 1
        assert results[0].id == "test_add_1"

    def test_add_multiple_documents(self, chromadb_store):
        docs = [
            IndexableDocument(id=str(i), text=f"doc {i}", embedding=[float(i)] * 3)
            for i in range(5)
        ]
        ids = chromadb_store.add_documents(docs)
        assert len(ids) == 5
        results = chromadb_store.similarity_search([0.0] * 3, k=10)
        assert len(results) == 5

    def test_update_document(self, chromadb_store):
        doc = IndexableDocument(
            id="update_test",
            text="original text",
            embedding=[0.1] * 3,
        )
        chromadb_store.add_documents([doc])
        updated = IndexableDocument(
            id="update_test",
            text="updated text",
            embedding=[0.2] * 3,
        )
        chromadb_store.update_documents([updated])
        results = chromadb_store.similarity_search([0.2] * 3, k=5)
        assert any(r.text == "updated text" for r in results)

    def test_delete_document(self, chromadb_store):
        docs = [
            IndexableDocument(id="del1", text="keep", embedding=[0.1] * 3),
            IndexableDocument(id="del2", text="delete", embedding=[0.2] * 3),
        ]
        chromadb_store.add_documents(docs)
        chromadb_store.delete_documents(["del2"])
        results = chromadb_store.similarity_search([0.0] * 3, k=10)
        ids = [r.id for r in results]
        assert "del1" in ids
        assert "del2" not in ids

    def test_delete_collection(self, chromadb_config):
        store = ChromaDBStore(config=chromadb_config)
        store.initialize()
        store.delete_collection(chromadb_config.collection_name)
        store.close()

    def test_similarity_search_with_score(self, chromadb_store):
        doc = IndexableDocument(
            id="score_test",
            text="score me",
            embedding=[0.5] * 3,
        )
        chromadb_store.add_documents([doc])
        results = chromadb_store.similarity_search_with_score([0.5] * 3, k=5)
        assert len(results) >= 1
        # Score should be near 1.0 for identical vectors
        assert results[0].score > 0.9

    def test_search_with_filter(self, chromadb_store):
        docs = [
            IndexableDocument(id="p1", text="patient 1", embedding=[0.1] * 3, patient_id="P001"),
            IndexableDocument(id="p2", text="patient 2", embedding=[0.1] * 3, patient_id="P002"),
        ]
        chromadb_store.add_documents(docs)
        results = chromadb_store.similarity_search(
            [0.1] * 3, k=5, filter={"patient_id": "P001"}
        )
        assert len(results) == 1
        assert results[0].id == "p1"

    def test_metadata_search(self, chromadb_store):
        docs = [
            IndexableDocument(id="m1", text="meta1", embedding=[0.1] * 3, patient_id="P001"),
            IndexableDocument(id="m2", text="meta2", embedding=[0.2] * 3, patient_id="P002"),
        ]
        chromadb_store.add_documents(docs)
        results = chromadb_store.metadata_search({"patient_id": "P001"}, k=10)
        assert len(results) == 1
        assert results[0].id == "m1"

    def test_list_collections(self, chromadb_store):
        collections = chromadb_store.list_collections()
        assert len(collections) >= 1
        assert any(c.name == "test_collection" for c in collections)

    def test_create_collection(self, chromadb_store):
        chromadb_store.create_collection("temp_collection")
        collections = chromadb_store.list_collections()
        names = [c.name for c in collections]
        assert "temp_collection" in names

    def test_create_duplicate_collection(self, chromadb_store):
        with pytest.raises(CollectionAlreadyExistsError):
            chromadb_store.create_collection("test_collection")

    def test_health_check_ok(self, chromadb_store):
        health = chromadb_store.health_check()
        assert health["status"] == "ok"
        assert health["provider"] == "chromadb"

    def test_health_check_error(self, chromadb_config):
        store = ChromaDBStore(config=chromadb_config)
        health = store.health_check()
        assert health["status"] == "error"

    def test_close(self, chromadb_store):
        chromadb_store.close()
        assert not chromadb_store._initialized

    def test_empty_add(self, chromadb_store):
        ids = chromadb_store.add_documents([])
        assert ids == []

    def test_empty_update(self, chromadb_store):
        chromadb_store.update_documents([])

    def test_empty_delete(self, chromadb_store):
        chromadb_store.delete_documents([])

    def test_hybrid_search(self, chromadb_store):
        doc = IndexableDocument(
            id="hybrid_test",
            text="hybrid search test",
            embedding=[0.3] * 3,
        )
        chromadb_store.add_documents([doc])
        results = chromadb_store.hybrid_search([0.3] * 3, "hybrid search", k=5)
        assert len(results) >= 1

    def test_add_with_full_metadata(self, chromadb_store):
        doc = IndexableDocument(
            id="full_meta",
            text="full metadata document",
            embedding=[0.7, 0.8, 0.9],
            document_type="discharge_summary",
            patient_id="P999",
            report_id="R888",
            section="medication",
            page=5,
            chunk_index=2,
            document_version="3.0.0",
            schema_version="2.0.0",
            embedding_version="v3",
            source="upload",
            language="de",
            provider="mock",
            extra={"ward": "ICU", "doctor": "Dr. Smith"},
        )
        chromadb_store.add_documents([doc])
        results = chromadb_store.similarity_search([0.7, 0.8, 0.9], k=5)
        assert len(results) >= 1
        meta = results[0].metadata
        assert meta.get("patient_id") == "P999"
        assert meta.get("report_id") == "R888"
        assert meta.get("section") == "medication"
        assert meta.get("page") == 5

    def test_filter_with_report_id(self, chromadb_store):
        docs = [
            IndexableDocument(id="r1", text="report 1", embedding=[0.1] * 3, report_id="R1"),
            IndexableDocument(id="r2", text="report 2", embedding=[0.1] * 3, report_id="R2"),
        ]
        chromadb_store.add_documents(docs)
        results = chromadb_store.similarity_search(
            [0.1] * 3, k=5, filter={"report_id": "R1"}
        )
        assert len(results) == 1
        assert results[0].id == "r1"

    def test_not_initialized_raises(self, chromadb_config):
        store = ChromaDBStore(config=chromadb_config)
        with pytest.raises(ProviderNotInitializedError):
            store.add_documents([IndexableDocument(id="x", text="x", embedding=[0.1])])

    def test_delete_nonexistent_no_error(self, chromadb_store):
        chromadb_store.delete_documents(["nonexistent_id"])


# =============================================================================
# VectorService Tests
# =============================================================================


@pytest.fixture
def mock_vector_service():
    store = MockVectorStore()
    store.initialize()
    emb = MockEmbeddingService()
    return VectorService(store=store, embedding_service=emb)


class TestVectorService:
    def test_index_chunks(self, mock_vector_service):
        meta = ChunkMetadata(
            chunk_index=0,
            document_type="note",
            patient_id="P001",
            report_id="R001",
            section="assessment",
            page=1,
            chunk_version="1.0",
            schema_version="1.0",
            source="ocr",
            language="en",
            provider="gemini",
        )
        chunk = DocumentChunk(
            text="Patient has diabetes",
            chunk_id="chunk_1",
            metadata=meta,
        )
        ids = mock_vector_service.index_chunks([chunk])
        assert len(ids) == 1

    def test_index_text(self, mock_vector_service):
        doc_id = mock_vector_service.index_text("Hello world", doc_id="text1")
        assert doc_id == "text1"

    def test_search(self, mock_vector_service):
        mock_vector_service.index_text("Diabetes symptoms", doc_id="s1")
        results = mock_vector_service.search("symptoms", k=5)
        assert len(results) >= 1

    def test_search_by_patient(self, mock_vector_service):
        mock_vector_service.index_text("Patient data", doc_id="p1")

        class MockFilterSearch:
            """Override to test patient search."""

        results = mock_vector_service.search_by_patient("P001", query="data", k=5)
        assert isinstance(results, list)

    def test_search_by_report(self, mock_vector_service):
        results = mock_vector_service.search_by_report("R001", query="test", k=5)
        assert isinstance(results, list)

    def test_search_by_document_type(self, mock_vector_service):
        results = mock_vector_service.search_by_document_type("note", query="test", k=5)
        assert isinstance(results, list)

    def test_delete(self, mock_vector_service):
        doc_id = mock_vector_service.index_text("Delete me", doc_id="del")
        mock_vector_service.delete([doc_id])
        results = mock_vector_service.search("Delete", k=5)
        assert all(r.id != doc_id for r in results)

    def test_list_collections(self, mock_vector_service):
        collections = mock_vector_service.list_collections()
        assert len(collections) >= 1

    def test_health_check(self, mock_vector_service):
        health = mock_vector_service.health_check()
        assert "vector_store" in health
        assert "embedding_service" in health

    def test_index_empty_chunks(self, mock_vector_service):
        ids = mock_vector_service.index_chunks([])
        assert ids == []

    def test_close(self, mock_vector_service):
        mock_vector_service.close()
        assert not mock_vector_service.store._initialized

    def test_store_property(self, mock_vector_service):
        assert isinstance(mock_vector_service.store, MockVectorStore)

    def test_embedding_service_property(self, mock_vector_service):
        assert isinstance(mock_vector_service.embedding_service, MockEmbeddingService)


# =============================================================================
# Future Provider Tests
# =============================================================================


class TestFutureProviders:
    @pytest.mark.parametrize("provider_name,expected_cls", [
        (QDRANT_PROVIDER_NAME, None),
        (WEAVIATE_PROVIDER_NAME, None),
        (PINECONE_PROVIDER_NAME, None),
    ])
    def test_future_providers_registered(self, provider_name, expected_cls):
        assert provider_name in VectorStoreRegistry.list_providers()

    def test_qdrant_not_implemented(self):
        config = VectorStoreConfig(provider=QDRANT_PROVIDER_NAME)
        store = VectorStoreRegistry.get(QDRANT_PROVIDER_NAME)(config=config)
        with pytest.raises(NotImplementedError):
            store.initialize()

    def test_weaviate_not_implemented(self):
        config = VectorStoreConfig(provider=WEAVIATE_PROVIDER_NAME)
        store = VectorStoreRegistry.get(WEAVIATE_PROVIDER_NAME)(config=config)
        with pytest.raises(NotImplementedError):
            store.initialize()

    def test_pinecone_not_implemented(self):
        config = VectorStoreConfig(provider=PINECONE_PROVIDER_NAME)
        store = VectorStoreRegistry.get(PINECONE_PROVIDER_NAME)(config=config)
        with pytest.raises(NotImplementedError):
            store.initialize()

    def test_future_provider_health_returns_error(self):
        for name in [QDRANT_PROVIDER_NAME, WEAVIATE_PROVIDER_NAME, PINECONE_PROVIDER_NAME]:
            config = VectorStoreConfig(provider=name)
            store = VectorStoreRegistry.get(name)(config=config)
            health = store.health_check()
            assert health["status"] == "error"


# =============================================================================
# Exception Tests
# =============================================================================


class TestExceptions:
    def test_base_exception(self):
        exc = VectorStoreError("base")
        assert isinstance(exc, Exception)

    def test_provider_not_found(self):
        exc = ProviderNotFoundError("not found")
        assert isinstance(exc, VectorStoreError)

    def test_provider_not_initialized(self):
        exc = ProviderNotInitializedError("not initialized")
        assert isinstance(exc, VectorStoreError)

    def test_collection_not_found(self):
        exc = CollectionNotFoundError("not found")
        assert isinstance(exc, VectorStoreError)

    def test_collection_already_exists(self):
        exc = CollectionAlreadyExistsError("exists")
        assert isinstance(exc, VectorStoreError)

    def test_document_operation_error(self):
        exc = DocumentOperationError("op failed")
        assert isinstance(exc, VectorStoreError)

    def test_search_error(self):
        exc = SearchError("search failed")
        assert isinstance(exc, VectorStoreError)

    def test_configuration_error(self):
        exc = ConfigurationError("bad config")
        assert isinstance(exc, VectorStoreError)

    def test_health_check_failed(self):
        exc = HealthCheckFailedError("unhealthy")
        assert isinstance(exc, VectorStoreError)
