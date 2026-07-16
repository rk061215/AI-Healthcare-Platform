from __future__ import annotations


class RetrievalError(Exception):
    """Base exception for the retrieval layer."""


class RetrieverNotFoundError(RetrievalError):
    """Raised when a requested retriever provider is not registered."""


class RetrieverNotInitializedError(RetrievalError):
    """Raised when trying to use an uninitialized retriever."""


class ConfigurationError(RetrievalError):
    """Raised when retriever configuration is invalid."""


class QueryError(RetrievalError):
    """Raised when a query is invalid or malformed."""


class SearchExecutionError(RetrievalError):
    """Raised when the underlying search operation fails."""


class HealthCheckFailedError(RetrievalError):
    """Raised when a provider health check fails."""


class FilterError(RetrievalError):
    """Raised when a filter parameter is invalid."""
