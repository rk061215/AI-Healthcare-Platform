from __future__ import annotations


class MemoryError(Exception):
    """Base exception for the memory module."""


class MemoryStoreError(MemoryError):
    """Error in the underlying memory store."""


class MemoryNotFoundError(MemoryError):
    """Requested memory entry does not exist."""


class MemoryTypeError(MemoryError):
    """Invalid memory type or unsupported memory operation."""


class MemoryFullError(MemoryError):
    """Memory store has reached its capacity limit."""


class MemoryExpiredError(MemoryError):
    """Memory entry has expired."""


class MemoryExtractionError(MemoryError):
    """Error during memory extraction."""


class MemoryRetrievalError(MemoryError):
    """Error during memory retrieval."""


class MemorySummarizationError(MemoryError):
    """Error during memory summarization."""


class MemoryPruningError(MemoryError):
    """Error during memory pruning."""


class PolicyViolationError(MemoryError):
    """Operation violates a memory policy."""


class RetentionPolicyViolationError(PolicyViolationError):
    """Operation violates retention policy."""


class PrivacyPolicyViolationError(PolicyViolationError):
    """Operation violates privacy policy."""


class ExpiryPolicyViolationError(PolicyViolationError):
    """Operation violates expiry policy."""


class SessionNotFoundError(MemoryError):
    """Session does not exist."""
