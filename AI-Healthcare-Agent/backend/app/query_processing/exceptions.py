from __future__ import annotations


class QueryProcessingError(Exception):
    """Base exception for query processing errors."""


class UnderstandingError(QueryProcessingError):
    """Raised when query understanding fails."""


class EntityExtractionError(QueryProcessingError):
    """Raised when entity extraction fails."""


class DecompositionError(QueryProcessingError):
    """Raised when question decomposition fails."""
