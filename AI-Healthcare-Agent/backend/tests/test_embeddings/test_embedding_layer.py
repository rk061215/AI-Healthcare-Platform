"""Tests for the provider-independent embedding layer (Phase B)."""

from unittest.mock import patch

import pytest

from app.embeddings import (
    EMBEDDING_SCHEMA_VERSION,
    BaseEmbedding,
    EmbeddingConfig,
    EmbeddingFactory,
    EmbeddingMetadata,
    EmbeddingRegistry,
    EmbeddingService,
    EmbeddingVersionInfo,
    MigrationResult,
    OutdatedEmbedding,
    ReEmbeddingResult,
    ReEmbeddingService,
)
# Import provider modules to trigger EmbeddingRegistry.register() calls
import app.embeddings.providers.gemini_embedding  # noqa: F401
import app.embeddings.providers.future.openai_embedding  # noqa: F401
import app.embeddings.providers.future.sentence_transformers_embedding  # noqa: F401
import app.embeddings.providers.future.voyage_embedding  # noqa: F401

from app.embeddings.exceptions import (
    BatchEmbeddingError,
    ConfigurationError,
    EmbeddingFailureError,
    HealthCheckFailedError,
    ProviderNotFoundError,
)


def _save_registry():
    """Snapshot current registry for test isolation."""
    return dict(EmbeddingRegistry._providers)


def _restore_registry(snapshot):
    EmbeddingRegistry.clear()
    EmbeddingRegistry._providers.update(snapshot)


# =============================================================================
# Mock provider for testing
# =============================================================================

class MockEmbedding(BaseEmbedding):
    """A mock embedding provider for testing the embedding layer."""

    def __init__(self, config=None):
        self._config = config or EmbeddingConfig()
        self._initialized = False
        self._fail_on_embed = False
        self._fail_on_batch = False

    def initialize(self):
        self._initialized = True

    def embed_text(self, text: str) -> list[float]:
        if not self._initialized:
            raise EmbeddingFailureError("Not initialized")
        if self._fail_on_embed:
            raise EmbeddingFailureError("Mock embed failure")
        return [0.1, 0.2, 0.3]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not self._initialized:
            raise EmbeddingFailureError("Not initialized")
        if self._fail_on_batch:
            raise EmbeddingFailureError("Mock batch failure")
        return [[0.1, 0.2, 0.3]] * len(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.embed_text(text)

    def dimension(self) -> int:
        return 3

    def model_name(self) -> str:
        return "mock-model-v1"

    def provider_name(self) -> str:
        return "mock"

    def health_check(self) -> dict:
        if not self._initialized:
            return {"status": "error", "error": "Not initialized"}
        return {"status": "ok", "error": None}


EmbeddingRegistry.register("mock", MockEmbedding)


# =============================================================================
# Registry Tests
# =============================================================================

class TestEmbeddingRegistry:
    def test_register_and_get(self):
        EmbeddingRegistry.register("test_provider", MockEmbedding)
        cls = EmbeddingRegistry.get("test_provider")
        assert cls is MockEmbedding
        EmbeddingRegistry.unregister("test_provider")

    def test_get_unregistered(self):
        assert EmbeddingRegistry.get("nonexistent") is None

    def test_list_providers(self):
        providers = EmbeddingRegistry.list_providers()
        assert "mock" in providers

    def test_register_lowercase(self):
        EmbeddingRegistry.register("UpperCase", MockEmbedding)
        assert EmbeddingRegistry.get("uppercase") is MockEmbedding
        EmbeddingRegistry.unregister("uppercase")

    def test_unregister(self):
        EmbeddingRegistry.register("temp", MockEmbedding)
        EmbeddingRegistry.unregister("temp")
        assert EmbeddingRegistry.get("temp") is None

    def test_clear(self):
        saved = _save_registry()
        EmbeddingRegistry.register("temp1", MockEmbedding)
        EmbeddingRegistry.register("temp2", MockEmbedding)
        EmbeddingRegistry.clear()
        assert EmbeddingRegistry.get("temp1") is None
        assert EmbeddingRegistry.get("temp2") is None
        _restore_registry(saved)


# =============================================================================
# Factory Tests
# =============================================================================

class TestEmbeddingFactory:
    def test_create_default(self):
        provider = EmbeddingFactory.create(provider_name="mock")
        assert isinstance(provider, MockEmbedding)
        assert provider._initialized

    def test_create_with_config(self):
        config = EmbeddingConfig(provider="mock", model="mock-model-v1")
        provider = EmbeddingFactory.create(config=config)
        assert isinstance(provider, MockEmbedding)
        assert provider._initialized

    def test_create_unregistered_raises(self):
        with pytest.raises(ProviderNotFoundError):
            EmbeddingFactory.create(provider_name="__nonexistent__")

    def test_create_overrides_config(self):
        config = EmbeddingConfig(provider="mock")
        provider = EmbeddingFactory.create(provider_name="mock", config=config)
        assert isinstance(provider, MockEmbedding)


# =============================================================================
# Provider Implementation Tests
# =============================================================================

class TestMockProvider:
    def test_embed_text(self):
        p = MockEmbedding()
        p.initialize()
        vec = p.embed_text("hello")
        assert len(vec) == 3
        assert vec == [0.1, 0.2, 0.3]

    def test_embed_batch(self):
        p = MockEmbedding()
        p.initialize()
        vecs = p.embed_batch(["a", "b", "c"])
        assert len(vecs) == 3
        assert all(len(v) == 3 for v in vecs)

    def test_embed_query(self):
        p = MockEmbedding()
        p.initialize()
        vec = p.embed_query("query")
        assert len(vec) == 3

    def test_dimension(self):
        p = MockEmbedding()
        assert p.dimension() == 3

    def test_model_name(self):
        p = MockEmbedding()
        assert p.model_name() == "mock-model-v1"

    def test_provider_name(self):
        p = MockEmbedding()
        assert p.provider_name() == "mock"

    def test_health_check_ok(self):
        p = MockEmbedding()
        p.initialize()
        result = p.health_check()
        assert result["status"] == "ok"

    def test_health_check_not_initialized(self):
        p = MockEmbedding()
        result = p.health_check()
        assert result["status"] == "error"

    def test_embed_text_not_initialized(self):
        p = MockEmbedding()
        with pytest.raises(EmbeddingFailureError, match="Not initialized"):
            p.embed_text("hello")

    def test_embed_batch_not_initialized(self):
        p = MockEmbedding()
        with pytest.raises(EmbeddingFailureError, match="Not initialized"):
            p.embed_batch(["hello"])

    def test_embed_empty_text(self):
        p = MockEmbedding()
        p.initialize()
        p._fail_on_embed = True
        with pytest.raises(EmbeddingFailureError):
            p.embed_text("hello")

    def test_batch_empty_list(self):
        p = MockEmbedding()
        p.initialize()
        assert p.embed_batch([]) == []


# =============================================================================
# Future Provider Skeleton Tests
# =============================================================================

class TestFutureProviders:
    def test_openai_registered(self):
        assert EmbeddingRegistry.get("openai") is not None

    def test_sentence_transformers_registered(self):
        assert EmbeddingRegistry.get("sentence_transformers") is not None
        assert EmbeddingRegistry.get("sentence-transformers") is not None

    def test_voyage_registered(self):
        assert EmbeddingRegistry.get("voyage") is not None

    def test_openai_not_implemented(self):
        from app.embeddings.providers.future.openai_embedding import OpenAIEmbedding
        p = OpenAIEmbedding()
        with pytest.raises(NotImplementedError):
            p.initialize()
        with pytest.raises(NotImplementedError):
            p.embed_text("test")

    def test_sentence_transformers_not_implemented(self):
        from app.embeddings.providers.future.sentence_transformers_embedding import (
            SentenceTransformersEmbedding,
        )
        p = SentenceTransformersEmbedding()
        with pytest.raises(NotImplementedError):
            p.initialize()

    def test_voyage_not_implemented(self):
        from app.embeddings.providers.future.voyage_embedding import VoyageEmbedding
        p = VoyageEmbedding()
        with pytest.raises(NotImplementedError):
            p.initialize()

    def test_openai_dimensions(self):
        from app.embeddings.providers.future.openai_embedding import OpenAIEmbedding
        p = OpenAIEmbedding()
        assert p.dimension() == 1536

    def test_sentence_transformers_dimensions(self):
        from app.embeddings.providers.future.sentence_transformers_embedding import (
            SentenceTransformersEmbedding,
        )
        p = SentenceTransformersEmbedding()
        assert p.dimension() == 384

    def test_voyage_dimensions(self):
        from app.embeddings.providers.future.voyage_embedding import VoyageEmbedding
        p = VoyageEmbedding()
        assert p.dimension() == 1024


# =============================================================================
# Metadata Tests
# =============================================================================

class TestEmbeddingMetadata:
    def test_default_creation(self):
        meta = EmbeddingMetadata(provider="mock", model="mock-v1", dimensions=3)
        assert meta.provider == "mock"
        assert meta.model == "mock-v1"
        assert meta.dimensions == 3
        assert meta.embedding_version == 1
        assert meta.schema_version == EMBEDDING_SCHEMA_VERSION
        assert meta.document_version == 1
        assert meta.created_at is not None
        assert meta.duration_ms is None

    def test_custom_versions(self):
        meta = EmbeddingMetadata(
            provider="gemini",
            model="text-embedding-004",
            dimensions=768,
            embedding_version=2,
            schema_version="2.0",
            document_version=3,
            duration_ms=45.2,
        )
        assert meta.embedding_version == 2
        assert meta.schema_version == "2.0"
        assert meta.document_version == 3
        assert meta.duration_ms == 45.2

    def test_serialization(self):
        meta = EmbeddingMetadata(provider="mock", model="mock-v1", dimensions=3)
        data = meta.model_dump()
        assert data["provider"] == "mock"
        assert data["dimensions"] == 3

    def test_outdated_embedding(self):
        o = OutdatedEmbedding(
            chunk_id="chunk-1",
            reason="embedding_version_mismatch",
            current_embedding_version=1,
            target_embedding_version=2,
            current_schema_version="1.0",
            target_schema_version="1.0",
            document_version=1,
            latest_document_version=2,
        )
        assert o.chunk_id == "chunk-1"
        assert o.reason == "embedding_version_mismatch"

    def test_reembedding_result(self):
        r = ReEmbeddingResult(
            total_chunks=10,
            succeeded=8,
            failed=2,
            errors=["chunk-3 failed", "chunk-7 failed"],
        )
        assert r.total_chunks == 10
        assert r.succeeded == 8
        assert r.failed == 2
        assert len(r.errors) == 2

    def test_migration_result(self):
        r = MigrationResult(
            previous_schema_version="1.0",
            target_schema_version="2.0",
            chunks_migrated=100,
            chunks_failed=0,
        )
        assert r.previous_schema_version == "1.0"
        assert r.target_schema_version == "2.0"
        assert r.chunks_migrated == 100

    def test_embedding_version_info(self):
        info = EmbeddingVersionInfo(
            embedding_version=1,
            schema_version="1.0",
            provider="gemini",
            model="text-embedding-004",
            dimensions=768,
        )
        assert info.provider == "gemini"
        assert info.dimensions == 768


# =============================================================================
# EmbeddingService Tests
# =============================================================================

class TestEmbeddingService:
    def test_embed_single(self):
        provider = MockEmbedding()
        provider.initialize()
        service = EmbeddingService(provider=provider)
        vector, meta = service.embed("test text")
        assert len(vector) == 3
        assert meta.provider == "mock"
        assert meta.dimensions == 3
        assert meta.duration_ms is not None

    def test_embed_batch(self):
        provider = MockEmbedding()
        provider.initialize()
        service = EmbeddingService(provider=provider)
        vectors, metas = service.embed_batch(["a", "b", "c"])
        assert len(vectors) == 3
        assert len(metas) == 3
        assert all(len(v) == 3 for v in vectors)
        assert all(m.provider == "mock" for m in metas)

    def test_embed_batch_empty(self):
        provider = MockEmbedding()
        provider.initialize()
        service = EmbeddingService(provider=provider)
        vectors, metas = service.embed_batch([])
        assert vectors == []
        assert metas == []

    def test_embed_query(self):
        provider = MockEmbedding()
        provider.initialize()
        service = EmbeddingService(provider=provider)
        vector, meta = service.embed_query("test query")
        assert len(vector) == 3
        assert meta.provider == "mock"

    def test_get_version_info(self):
        provider = MockEmbedding()
        provider.initialize()
        service = EmbeddingService(provider=provider)
        info = service.get_version_info()
        assert info.provider == "mock"
        assert info.dimensions == 3
        assert info.schema_version == EMBEDDING_SCHEMA_VERSION

    def test_health_check(self):
        provider = MockEmbedding()
        provider.initialize()
        service = EmbeddingService(provider=provider)
        result = service.health_check()
        assert result["status"] == "ok"

    def test_provider_property(self):
        provider = MockEmbedding()
        provider.initialize()
        service = EmbeddingService(provider=provider)
        assert service.provider is provider

    def test_batch_failure_raises(self):
        provider = MockEmbedding()
        provider.initialize()
        provider._fail_on_batch = True
        service = EmbeddingService(provider=provider)
        with pytest.raises(BatchEmbeddingError):
            service.embed_batch(["a", "b"])


# =============================================================================
# ReEmbeddingService Interface Tests
# =============================================================================

class TestReEmbeddingServiceInterface:
    def test_abstract_methods(self):
        import inspect
        methods = [
            "detect_outdated",
            "reembed",
            "get_version_info",
            "migrate_schema",
        ]
        for method in methods:
            assert hasattr(ReEmbeddingService, method)
            assert getattr(ReEmbeddingService, method).__isabstractmethod__

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            ReEmbeddingService()


# =============================================================================
# Configuration Tests
# =============================================================================

class TestEmbeddingConfig:
    def test_default_config(self):
        config = EmbeddingConfig()
        assert config.provider == "gemini" or config.provider != ""

    def test_custom_config(self):
        config = EmbeddingConfig(
            provider="openai",
            model="text-embedding-3-small",
            dimension=1536,
            batch_size=50,
        )
        assert config.provider == "openai"
        assert config.model == "text-embedding-3-small"
        assert config.dimension == 1536
        assert config.batch_size == 50


# =============================================================================
# Gemini Embedding Provider — integration check (no API key in CI)
# =============================================================================

class TestGeminiEmbedding:
    def test_import_and_registered(self):
        from app.embeddings.providers.gemini_embedding import GeminiEmbedding
        assert EmbeddingRegistry.get("gemini") is GeminiEmbedding

    def test_dimension_default(self):
        from app.embeddings.providers.gemini_embedding import GeminiEmbedding
        p = GeminiEmbedding()
        assert p.dimension() == 768

    def test_dimension_known_models(self):
        from app.embeddings.providers.gemini_embedding import GeminiEmbedding
        models = {
            "text-embedding-004": 768,
            "text-embedding-005": 768,
            "text-embedding-001": 768,
            "text-embedding-gecko": 768,
        }
        for model, expected_dim in models.items():
            p = GeminiEmbedding(config=EmbeddingConfig(model=model))
            assert p.dimension() == expected_dim, f"{model} should be {expected_dim}"

    def test_model_name(self):
        from app.embeddings.providers.gemini_embedding import GeminiEmbedding
        p = GeminiEmbedding(config=EmbeddingConfig(model="text-embedding-004"))
        assert p.model_name() == "text-embedding-004"

    def test_provider_name(self):
        from app.embeddings.providers.gemini_embedding import GeminiEmbedding
        p = GeminiEmbedding()
        assert p.provider_name() == "gemini"

    def test_health_check_not_initialized(self):
        from app.embeddings.providers.gemini_embedding import GeminiEmbedding
        p = GeminiEmbedding()
        result = p.health_check()
        assert result["status"] == "error"
        assert "Not initialized" in result["error"]

    def test_initialize_no_api_key(self):
        from app.embeddings.providers.gemini_embedding import GeminiEmbedding
        p = GeminiEmbedding(config=EmbeddingConfig(api_key=""))
        with pytest.raises(EmbeddingFailureError, match="API key"):
            p.initialize()
