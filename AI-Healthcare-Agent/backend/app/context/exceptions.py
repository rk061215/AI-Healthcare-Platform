from __future__ import annotations


class ContextError(Exception):
    """Base exception for the context building layer."""


class ConfigurationError(ContextError):
    """Raised when context configuration is invalid."""


class TokenBudgetExceededError(ContextError):
    """Raised when context exceeds the maximum token budget."""


class EmptyContextError(ContextError):
    """Raised when no fragments are provided for context building."""


class DeduplicationError(ContextError):
    """Raised when deduplication fails."""


class CompressionError(ContextError):
    """Raised when compression or merging fails."""


class CitationError(ContextError):
    """Raised when citation generation fails."""


class RankingError(ContextError):
    """Raised when ranking fails."""
