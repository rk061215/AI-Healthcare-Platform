from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class EmbeddingError(Exception):
    """Base exception for the embedding layer."""


class ProviderNotFoundError(EmbeddingError):
    """Raised when a requested embedding provider is not registered."""


class ProviderNotInitializedError(EmbeddingError):
    """Raised when trying to use an uninitialized embedding provider."""


class EmbeddingFailureError(EmbeddingError):
    """Raised when embedding generation fails."""


class BatchEmbeddingError(EmbeddingError):
    """Raised when batch embedding partially or fully fails."""


class ConfigurationError(EmbeddingError):
    """Raised when embedding configuration is invalid."""


class HealthCheckFailedError(EmbeddingError):
    """Raised when a provider health check fails."""


class ReEmbeddingError(EmbeddingError):
    """Raised when re-embedding operations fail."""


class SchemaMigrationError(EmbeddingError):
    """Raised when embedding schema migration fails."""
