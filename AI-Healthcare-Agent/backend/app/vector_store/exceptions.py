from __future__ import annotations


class VectorStoreError(Exception):
    """Base exception for the vector store layer."""


class ProviderNotFoundError(VectorStoreError):
    """Raised when a requested vector store provider is not registered."""


class ProviderNotInitializedError(VectorStoreError):
    """Raised when trying to use an uninitialized vector store provider."""


class CollectionNotFoundError(VectorStoreError):
    """Raised when a requested collection does not exist."""


class CollectionAlreadyExistsError(VectorStoreError):
    """Raised when trying to create a collection that already exists."""


class DocumentOperationError(VectorStoreError):
    """Raised when a document add/update/delete operation fails."""


class SearchError(VectorStoreError):
    """Raised when a search operation fails."""


class ConfigurationError(VectorStoreError):
    """Raised when vector store configuration is invalid."""


class HealthCheckFailedError(VectorStoreError):
    """Raised when a provider health check fails."""


class EmbeddingDimensionMismatchError(VectorStoreError):
    """Raised when embedding dimension does not match collection dimension."""


class VersionConflictError(VectorStoreError):
    """Raised when a document version conflict is detected."""
