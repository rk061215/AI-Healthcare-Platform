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
from app.retrieval.providers.hybrid_retriever import (
    HYBRID_RETRIEVER_PROVIDER_NAME,
    HybridRetriever,
)
from app.retrieval.providers.keyword_retriever import (
    KEYWORD_RETRIEVER_PROVIDER_NAME,
    KeywordRetriever,
)
from app.retrieval.providers.multi_query_retriever import (
    MULTI_QUERY_RETRIEVER_PROVIDER_NAME,
    MultiQueryRetriever,
)
from app.retrieval.context_compressor import ContextCompressor
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.reranking import Reranker
from app.retrieval.retriever_registry import RetrieverRegistry
from app.retrieval.retriever_factory import RetrieverFactory
from app.retrieval.retriever_service import RetrieverService

RetrieverRegistry.register(VECTOR_RETRIEVER_PROVIDER_NAME, VectorRetriever)
RetrieverRegistry.register(HYBRID_RETRIEVER_PROVIDER_NAME, HybridRetriever)
RetrieverRegistry.register(KEYWORD_RETRIEVER_PROVIDER_NAME, KeywordRetriever)
RetrieverRegistry.register(MULTI_QUERY_RETRIEVER_PROVIDER_NAME, MultiQueryRetriever)

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
    "MULTI_QUERY_RETRIEVER_PROVIDER_NAME",
    "MultiQueryRetriever",
    "RetrieverRegistry",
    "RetrieverFactory",
    "RetrieverService",
    "Reranker",
    "ContextCompressor",
    "reciprocal_rank_fusion",
]
