from app.vector_store.base_vector_store import BaseVectorStore
from app.vector_store.config import VectorStoreConfig
from app.vector_store.exceptions import (
    CollectionAlreadyExistsError,
    CollectionNotFoundError,
    ConfigurationError,
    DocumentOperationError,
    HealthCheckFailedError,
    ProviderNotInitializedError,
    ProviderNotFoundError,
    SearchError,
)
from app.vector_store.models import (
    CollectionInfo,
    IndexableDocument,
    SearchFilter,
    SearchResult,
)
from app.vector_store.providers.chromadb_store import (
    CHROMADB_PROVIDER_NAME,
    ChromaDBStore,
)
from app.vector_store.providers.future.qdrant_store import (
    QDRANT_PROVIDER_NAME,
    QdrantStore,
)
from app.vector_store.providers.future.weaviate_store import (
    WEAVIATE_PROVIDER_NAME,
    WeaviateStore,
)
from app.vector_store.providers.future.pinecone_store import (
    PINECONE_PROVIDER_NAME,
    PineconeStore,
)
from app.vector_store.vector_store_registry import VectorStoreRegistry
from app.vector_store.vector_store_factory import VectorStoreFactory
from app.vector_store.vector_service import VectorService

VectorStoreRegistry.register(CHROMADB_PROVIDER_NAME, ChromaDBStore)
VectorStoreRegistry.register(QDRANT_PROVIDER_NAME, QdrantStore)
VectorStoreRegistry.register(WEAVIATE_PROVIDER_NAME, WeaviateStore)
VectorStoreRegistry.register(PINECONE_PROVIDER_NAME, PineconeStore)

__all__ = [
    "BaseVectorStore",
    "VectorStoreConfig",
    "CollectionAlreadyExistsError",
    "CollectionNotFoundError",
    "ConfigurationError",
    "DocumentOperationError",
    "HealthCheckFailedError",
    "ProviderNotInitializedError",
    "ProviderNotFoundError",
    "SearchError",
    "CollectionInfo",
    "IndexableDocument",
    "SearchFilter",
    "SearchResult",
    "CHROMADB_PROVIDER_NAME",
    "ChromaDBStore",
    "QDRANT_PROVIDER_NAME",
    "QdrantStore",
    "WEAVIATE_PROVIDER_NAME",
    "WeaviateStore",
    "PINECONE_PROVIDER_NAME",
    "PineconeStore",
    "VectorStoreRegistry",
    "VectorStoreFactory",
    "VectorService",
]
