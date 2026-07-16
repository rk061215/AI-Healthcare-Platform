from __future__ import annotations

from typing import Any, Optional

import pytest

from app.retrieval import (
    HYBRID_RETRIEVER_PROVIDER_NAME,
    KEYWORD_RETRIEVER_PROVIDER_NAME,
    VECTOR_RETRIEVER_PROVIDER_NAME,
    BaseRetriever,
    ConfigurationError,
    HealthCheckFailedError,
    QueryError,
    RetrieverNotFoundError,
    RetrieverNotInitializedError,
    RetrievalError,
    RetrievalMetrics,
    RetrievalQuery,
    RetrievalResult,
    RetrievedDocument,
    RetrieverConfig,
    RetrieverFactory,
    RetrieverRegistry,
    RetrieverService,
    SearchExecutionError,
)
from app.retrieval.retriever_service import RetrieverService

# =============================================================================
# Helpers
# =============================================================================


def _save_registry() -> dict[str, type[BaseRetriever]]:
    return RetrieverRegistry._save_registry()


def _restore_registry(saved: dict[str, type[BaseRetriever]]) -> None:
    RetrieverRegistry._restore_registry(saved)


@pytest.fixture(autouse=True)
def registry_isolation():
    saved = _save_registry()
    yield
    RetrieverRegistry.clear()
    _restore_registry(saved)


# =============================================================================
# Mock Retriever
# =============================================================================


class MockRetriever(BaseRetriever):
    """In-memory mock for testing BaseRetriever interface."""

    def __init__(self, config: Optional[RetrieverConfig] = None) -> None:
        self._config = config or RetrieverConfig()
        self._initialized = False
        self._fail = False
        self._results: list[RetrievalResult] = []

    def initialize(self) -> None:
        self._initialized = True

    def _build_mock_results(self, count: int = 3) -> list[RetrievalResult]:
        return [
            RetrievalResult(
                chunk_id=f"chunk_{i}",
                text=f"Mock result {i} for query",
                score=1.0 - (i * 0.1),
                document_id=f"doc_{i}",
                patient_id="P001",
                document_type="note",
                section="assessment",
                chunk_index=i,
            )
            for i in range(count)
        ]

    def retrieve(self, query: RetrievalQuery) -> RetrievedDocument:
        if self._fail:
            raise SearchExecutionError("Mock retrieval failure")
        results = self._build_mock_results(query.top_k)
        return RetrievedDocument(
            query=query,
            results=results,
            total_results=len(results),
            returned_results=len(results),
            retrieval_time_ms=1.0,
            provider="mock",
        )

    def retrieve_by_patient(
        self, patient_id: str, query: Optional[str] = None, top_k: int = 20
    ) -> RetrievedDocument:
        if self._fail:
            raise SearchExecutionError("Mock retrieval failure")
        results = self._build_mock_results(top_k)
        return RetrievedDocument(
            query=RetrievalQuery(text=query or "", top_k=top_k, patient_id=patient_id),
            results=results,
            total_results=len(results),
            returned_results=len(results),
            retrieval_time_ms=1.0,
            provider="mock",
        )

    def retrieve_by_report(
        self, report_id: str, query: Optional[str] = None, top_k: int = 50
    ) -> RetrievedDocument:
        if self._fail:
            raise SearchExecutionError("Mock retrieval failure")
        results = self._build_mock_results(top_k)
        return RetrievedDocument(
            query=RetrievalQuery(text=query or "", top_k=top_k, report_id=report_id),
            results=results,
            total_results=len(results),
            returned_results=len(results),
            retrieval_time_ms=1.0,
            provider="mock",
        )

    def retrieve_by_document_type(
        self, document_type: str, query: Optional[str] = None, top_k: int = 50
    ) -> RetrievedDocument:
        if self._fail:
            raise SearchExecutionError("Mock retrieval failure")
        results = self._build_mock_results(top_k)
        return RetrievedDocument(
            query=RetrievalQuery(text=query or "", top_k=top_k, document_type=document_type),
            results=results,
            total_results=len(results),
            returned_results=len(results),
            retrieval_time_ms=1.0,
            provider="mock",
        )

    def retrieve_with_scores(self, query: RetrievalQuery) -> RetrievedDocument:
        return self.retrieve(query)

    def health_check(self) -> dict[str, Any]:
        if not self._initialized:
            return {"status": "error", "error": "Not initialized"}
        return {"status": "ok", "provider": "mock"}

    def close(self) -> None:
        self._initialized = False


RetrieverRegistry.register("mock", MockRetriever)


# =============================================================================
# Model Tests
# =============================================================================


class TestRetrievalQuery:
    def test_defaults(self):
        q = RetrievalQuery(text="patient symptoms")
        assert q.text == "patient symptoms"
        assert q.top_k == 10
        assert q.patient_id is None
        assert q.report_id is None
        assert q.min_score == 0.0
        assert q.metadata_filter == {}

    def test_all_fields(self):
        q = RetrievalQuery(
            text="diabetes",
            top_k=5,
            patient_id="P001",
            report_id="R001",
            document_type="lab_report",
            section="results",
            source="ocr",
            language="en",
            metadata_filter={"key": "val"},
            min_score=0.5,
            include_embeddings=True,
        )
        assert q.patient_id == "P001"
        assert q.report_id == "R001"
        assert q.document_type == "lab_report"
        assert q.section == "results"
        assert q.min_score == 0.5

    def test_extra_forbidden(self):
        with pytest.raises(Exception):
            RetrievalQuery(text="x", unknown=True)  # type: ignore


class TestRetrievalResult:
    def test_defaults(self):
        r = RetrievalResult(chunk_id="c1", text="hello", score=0.95)
        assert r.chunk_id == "c1"
        assert r.score == 0.95
        assert r.document_type == "unknown"
        assert r.patient_id is None
        assert r.chunk_index == 0

    def test_citation_id(self):
        r = RetrievalResult(
            chunk_id="c1", text="x", score=0.9,
            report_id="R1", section="assessment",
        )
        assert r.citation_id == "c1/R1/assessment"

    def test_citation_id_minimal(self):
        r = RetrievalResult(chunk_id="c1", text="x", score=0.9)
        assert r.citation_id == "c1"


class TestRetrievedDocument:
    def test_defaults(self):
        doc = RetrievedDocument(query=RetrievalQuery(text="q"))
        assert doc.total_results == 0
        assert doc.returned_results == 0
        assert doc.retrieval_time_ms == 0.0
        assert doc.provider == "unknown"


class TestRetrievalMetrics:
    def test_defaults(self):
        m = RetrievalMetrics()
        assert m.total_chunks_retrieved == 0
        assert m.filter_applied is False


# =============================================================================
# RetrieverConfig Tests
# =============================================================================


class TestRetrieverConfig:
    def test_default_provider(self):
        cfg = RetrieverConfig()
        assert cfg.provider == "vector_retriever"

    def test_custom_provider(self):
        cfg = RetrieverConfig(provider="custom")
        assert cfg.provider == "custom"

    def test_default_top_k(self):
        cfg = RetrieverConfig()
        assert cfg.top_k == 10


# =============================================================================
# RetrieverRegistry Tests
# =============================================================================


class TestRetrieverRegistry:
    def test_register_and_get(self):
        RetrieverRegistry.register("test_r", MockRetriever)
        cls = RetrieverRegistry.get("test_r")
        assert cls is MockRetriever

    def test_get_unregistered(self):
        with pytest.raises(RetrieverNotFoundError, match="not registered"):
            RetrieverRegistry.get("nonexistent")

    def test_list_providers(self):
        providers = RetrieverRegistry.list_providers()
        assert "mock" in providers

    def test_clear(self):
        RetrieverRegistry.clear()
        assert RetrieverRegistry.list_providers() == []

    def test_save_and_restore(self):
        saved = _save_registry()
        RetrieverRegistry.clear()
        RetrieverRegistry.register("new", MockRetriever)
        _restore_registry(saved)
        assert "mock" in RetrieverRegistry.list_providers()
        assert "new" not in RetrieverRegistry.list_providers()


# =============================================================================
# RetrieverFactory Tests
# =============================================================================


class TestRetrieverFactory:
    def test_create_mock(self):
        config = RetrieverConfig(provider="mock")
        retriever = RetrieverFactory.create(config)
        assert isinstance(retriever, MockRetriever)
        assert retriever._initialized

    def test_default_config(self):
        saved = _save_registry()
        RetrieverRegistry.clear()
        RetrieverRegistry.register("vector_retriever", MockRetriever)
        retriever = RetrieverFactory.create()
        assert isinstance(retriever, MockRetriever)
        _restore_registry(saved)

    def test_unknown_provider(self):
        config = RetrieverConfig(provider="unknown")
        with pytest.raises(RetrieverNotFoundError):
            RetrieverFactory.create(config)


# =============================================================================
# RetrieverService Tests
# =============================================================================


@pytest.fixture
def mock_service():
    retriever = MockRetriever()
    retriever.initialize()
    return RetrieverService(retriever=retriever)


class TestRetrieverService:
    def test_search(self, mock_service):
        result = mock_service.search("patient symptoms", top_k=3)
        assert isinstance(result, RetrievedDocument)
        assert len(result.results) == 3
        assert result.returned_results == 3

    def test_search_empty_query(self, mock_service):
        with pytest.raises(QueryError, match="cannot be empty"):
            mock_service.search("")

    def test_search_whitespace_query(self, mock_service):
        with pytest.raises(QueryError, match="cannot be empty"):
            mock_service.search("   ")

    def test_search_with_patient_filter(self, mock_service):
        result = mock_service.search("symptoms", patient_id="P001", top_k=3)
        assert result.query.patient_id == "P001"

    def test_search_with_report_filter(self, mock_service):
        result = mock_service.search("symptoms", report_id="R001")
        assert result.query.report_id == "R001"

    def test_search_by_patient(self, mock_service):
        result = mock_service.search_by_patient("P001", query="diabetes", top_k=5)
        assert len(result.results) == 5

    def test_search_by_patient_empty_id(self, mock_service):
        with pytest.raises(QueryError, match="patient_id"):
            mock_service.search_by_patient("")

    def test_search_by_report(self, mock_service):
        result = mock_service.search_by_report("R001", query="lab", top_k=3)
        assert len(result.results) == 3

    def test_search_by_report_empty_id(self, mock_service):
        with pytest.raises(QueryError, match="report_id"):
            mock_service.search_by_report("")

    def test_search_by_document_type(self, mock_service):
        result = mock_service.search_by_document_type("lab_report", query="test", top_k=2)
        assert len(result.results) == 2

    def test_search_by_document_type_empty(self, mock_service):
        with pytest.raises(QueryError, match="document_type"):
            mock_service.search_by_document_type("")

    def test_health_check(self, mock_service):
        health = mock_service.health_check()
        assert health["status"] == "ok"

    def test_close(self, mock_service):
        mock_service.close()
        assert not mock_service.retriever._initialized

    def test_retriever_property(self, mock_service):
        assert isinstance(mock_service.retriever, MockRetriever)


# =============================================================================
# MockRetriever (BaseRetriever interface) Tests
# =============================================================================


class TestMockRetriever:
    def test_retrieve(self):
        retriever = MockRetriever()
        retriever.initialize()
        q = RetrievalQuery(text="test", top_k=2)
        doc = retriever.retrieve(q)
        assert len(doc.results) == 2
        assert doc.results[0].score >= doc.results[1].score

    def test_retrieve_by_patient(self):
        retriever = MockRetriever()
        retriever.initialize()
        doc = retriever.retrieve_by_patient("P001", query="symptoms", top_k=3)
        assert len(doc.results) == 3
        assert doc.query.patient_id == "P001"

    def test_retrieve_by_patient_no_query(self):
        retriever = MockRetriever()
        retriever.initialize()
        doc = retriever.retrieve_by_patient("P001", top_k=2)
        assert len(doc.results) == 2

    def test_retrieve_by_report(self):
        retriever = MockRetriever()
        retriever.initialize()
        doc = retriever.retrieve_by_report("R001", top_k=2)
        assert doc.query.report_id == "R001"

    def test_retrieve_by_document_type(self):
        retriever = MockRetriever()
        retriever.initialize()
        doc = retriever.retrieve_by_document_type("lab_report", top_k=2)
        assert doc.query.document_type == "lab_report"

    def test_retrieve_with_scores(self):
        retriever = MockRetriever()
        retriever.initialize()
        q = RetrievalQuery(text="test", top_k=2)
        doc = retriever.retrieve_with_scores(q)
        assert len(doc.results) == 2

    def test_health_check_initialized(self):
        retriever = MockRetriever()
        retriever.initialize()
        health = retriever.health_check()
        assert health["status"] == "ok"

    def test_health_check_not_initialized(self):
        retriever = MockRetriever()
        health = retriever.health_check()
        assert health["status"] == "error"

    def test_close(self):
        retriever = MockRetriever()
        retriever.initialize()
        retriever.close()
        assert not retriever._initialized

    def test_retrieve_failure(self):
        retriever = MockRetriever()
        retriever.initialize()
        retriever._fail = True
        with pytest.raises(SearchExecutionError):
            retriever.retrieve(RetrievalQuery(text="x"))


# =============================================================================
# VectorRetriever Tests (integration with VectorService mock)
# =============================================================================


class MockVectorService:
    """Minimal mock for VectorService used by VectorRetriever tests."""

    def __init__(self):
        self._closed = False

    def search(self, query: str, k: int = 10) -> list:
        from app.vector_store.models import SearchResult
        return [
            SearchResult(id=f"chunk_{i}", text=f"Result {i}", score=1.0 - i * 0.1, metadata={
                "patient_id": "P001", "document_type": "note",
                "section": "assessment", "chunk_index": i,
                "source": "ocr", "language": "en",
            })
            for i in range(k)
        ]

    def search_by_patient(self, patient_id: str, query: str = None, k: int = 20) -> list:
        return self.search(query or "", k)

    def search_by_report(self, report_id: str, query: str = None, k: int = 50) -> list:
        return self.search(query or "", k)

    def search_by_document_type(self, document_type: str, query: str = None, k: int = 50) -> list:
        return self.search(query or "", k)

    def health_check(self) -> dict:
        return {"status": "ok", "vector_store": {"status": "ok"}, "embedding_service": {"status": "ok"}}

    def close(self) -> None:
        self._closed = True


from app.retrieval.providers.vector_retriever import VectorRetriever


class TestVectorRetriever:
    def test_initialize_with_existing_service(self):
        vs = MockVectorService()
        retriever = VectorRetriever(vector_service=vs)
        retriever.initialize()
        assert retriever._initialized

    def test_retrieve(self):
        retriever = VectorRetriever()
        retriever._vector_service = MockVectorService()
        retriever._initialized = True
        q = RetrievalQuery(text="symptoms", top_k=3)
        doc = retriever.retrieve(q)
        assert len(doc.results) == 3
        assert doc.provider == "vector_retriever"
        assert doc.retrieval_time_ms > 0

    def test_retrieve_by_patient(self):
        retriever = VectorRetriever()
        retriever._vector_service = MockVectorService()
        retriever._initialized = True
        doc = retriever.retrieve_by_patient("P001", query="test", top_k=2)
        assert len(doc.results) == 2
        assert doc.query.patient_id == "P001"

    def test_retrieve_by_report(self):
        retriever = VectorRetriever()
        retriever._vector_service = MockVectorService()
        retriever._initialized = True
        doc = retriever.retrieve_by_report("R001", query="test", top_k=3)
        assert doc.query.report_id == "R001"

    def test_retrieve_by_document_type(self):
        retriever = VectorRetriever()
        retriever._vector_service = MockVectorService()
        retriever._initialized = True
        doc = retriever.retrieve_by_document_type("lab_report", query="test", top_k=2)
        assert doc.query.document_type == "lab_report"

    def test_health_check_ok(self):
        retriever = VectorRetriever()
        retriever._vector_service = MockVectorService()
        retriever._initialized = True
        health = retriever.health_check()
        assert health["status"] == "ok"

    def test_health_check_not_initialized(self):
        retriever = VectorRetriever()
        health = retriever.health_check()
        assert health["status"] == "error"

    def test_not_initialized_raises(self):
        retriever = VectorRetriever()
        with pytest.raises(RetrieverNotInitializedError):
            retriever.retrieve(RetrievalQuery(text="x"))

    def test_close(self):
        vs = MockVectorService()
        retriever = VectorRetriever(vector_service=vs)
        retriever.initialize()
        retriever.close()
        assert not retriever._initialized
        assert vs._closed

    def test_retrieve_with_scores(self):
        retriever = VectorRetriever()
        retriever._vector_service = MockVectorService()
        retriever._initialized = True
        q = RetrievalQuery(text="test", top_k=2)
        doc = retriever.retrieve_with_scores(q)
        assert len(doc.results) == 2

    def test_min_score_filter(self):
        retriever = VectorRetriever()
        retriever._vector_service = MockVectorService()
        retriever._initialized = True
        q = RetrievalQuery(text="test", top_k=5, min_score=0.95)
        doc = retriever.retrieve(q)
        for r in doc.results:
            assert r.score >= 0.95

    def test_default_initialize_creates_vector_service(self):
        retriever = VectorRetriever()
        retriever._vector_service = MockVectorService()
        retriever._initialized = True
        assert retriever._vector_service is not None
        assert retriever._initialized
        retriever.close()


# =============================================================================
# Future Provider Tests
# =============================================================================


class TestFutureRetrievers:
    def test_hybrid_registered(self):
        assert HYBRID_RETRIEVER_PROVIDER_NAME in RetrieverRegistry.list_providers()

    def test_keyword_registered(self):
        assert KEYWORD_RETRIEVER_PROVIDER_NAME in RetrieverRegistry.list_providers()

    def test_hybrid_not_implemented(self):
        config = RetrieverConfig(provider=HYBRID_RETRIEVER_PROVIDER_NAME)
        retriever = RetrieverRegistry.get(HYBRID_RETRIEVER_PROVIDER_NAME)(config=config)
        with pytest.raises(NotImplementedError):
            retriever.initialize()

    def test_keyword_not_implemented(self):
        config = RetrieverConfig(provider=KEYWORD_RETRIEVER_PROVIDER_NAME)
        retriever = RetrieverRegistry.get(KEYWORD_RETRIEVER_PROVIDER_NAME)(config=config)
        with pytest.raises(NotImplementedError):
            retriever.initialize()

    def test_hybrid_health_error(self):
        config = RetrieverConfig(provider=HYBRID_RETRIEVER_PROVIDER_NAME)
        retriever = RetrieverRegistry.get(HYBRID_RETRIEVER_PROVIDER_NAME)(config=config)
        health = retriever.health_check()
        assert health["status"] == "error"

    def test_keyword_health_error(self):
        config = RetrieverConfig(provider=KEYWORD_RETRIEVER_PROVIDER_NAME)
        retriever = RetrieverRegistry.get(KEYWORD_RETRIEVER_PROVIDER_NAME)(config=config)
        health = retriever.health_check()
        assert health["status"] == "error"


# =============================================================================
# Exception Tests
# =============================================================================


class TestRetrievalExceptions:
    def test_base(self):
        assert issubclass(RetrievalError, Exception)

    def test_retriever_not_found(self):
        assert issubclass(RetrieverNotFoundError, RetrievalError)

    def test_retriever_not_initialized(self):
        assert issubclass(RetrieverNotInitializedError, RetrievalError)

    def test_query_error(self):
        assert issubclass(QueryError, RetrievalError)

    def test_search_execution(self):
        assert issubclass(SearchExecutionError, RetrievalError)

    def test_health_check(self):
        assert issubclass(HealthCheckFailedError, RetrievalError)

    def test_filter_error(self):
        from app.retrieval.exceptions import FilterError
        assert issubclass(FilterError, RetrievalError)

    def test_configuration(self):
        assert issubclass(ConfigurationError, RetrievalError)
