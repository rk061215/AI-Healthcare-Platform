from app.retrieval.base_retriever import BaseRetriever
from app.retrieval.config import RetrieverConfig
from app.retrieval.exceptions import (
    ConfigurationError,
    FilterError,
    HealthCheckFailedError,
    QueryError,
    RetrieverNotFoundError,
    RetrieverNotInitializedError,
    RetrievalError,
    SearchExecutionError,
)
from app.retrieval.models import (
    RETRIEVAL_SCHEMA_VERSION,
    RetrievalMetrics,
    RetrievalQuery,
    RetrievalResult,
    RetrievedDocument,
)
from app.retrieval.providers.vector_retriever import (
    VECTOR_RETRIEVER_PROVIDER_NAME,
    VectorRetriever,
)
from app.retrieval.providers.future.hybrid_retriever import (
    HYBRID_RETRIEVER_PROVIDER_NAME,
    HybridRetriever,
)
from app.retrieval.providers.future.keyword_retriever import (
    KEYWORD_RETRIEVER_PROVIDER_NAME,
    KeywordRetriever,
)
from app.retrieval.retriever_registry import RetrieverRegistry
from app.retrieval.retriever_factory import RetrieverFactory
from app.retrieval.retriever_service import RetrieverService

RetrieverRegistry.register(VECTOR_RETRIEVER_PROVIDER_NAME, VectorRetriever)
RetrieverRegistry.register(HYBRID_RETRIEVER_PROVIDER_NAME, HybridRetriever)
RetrieverRegistry.register(KEYWORD_RETRIEVER_PROVIDER_NAME, KeywordRetriever)

__all__ = [
    "BaseRetriever",
    "RetrieverConfig",
    "ConfigurationError",
    "FilterError",
    "HealthCheckFailedError",
    "QueryError",
    "RetrieverNotFoundError",
    "RetrieverNotInitializedError",
    "RetrievalError",
    "SearchExecutionError",
    "RETRIEVAL_SCHEMA_VERSION",
    "RetrievalMetrics",
    "RetrievalQuery",
    "RetrievalResult",
    "RetrievedDocument",
    "VECTOR_RETRIEVER_PROVIDER_NAME",
    "VectorRetriever",
    "HYBRID_RETRIEVER_PROVIDER_NAME",
    "HybridRetriever",
    "KEYWORD_RETRIEVER_PROVIDER_NAME",
    "KeywordRetriever",
    "RetrieverRegistry",
    "RetrieverFactory",
    "RetrieverService",
]
