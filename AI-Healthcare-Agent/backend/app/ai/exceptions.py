class AIProviderError(Exception):
    """Base exception for all AI provider errors."""


class ProviderNotFoundError(AIProviderError):
    """Raised when a requested provider is not registered."""


class ProviderNotInitializedError(AIProviderError):
    """Raised when trying to use an uninitialized provider."""


class QuotaExceededError(AIProviderError):
    """Raised when API quota or rate limit is exceeded."""


class TimeoutError(AIProviderError):
    """Raised when a provider request times out."""


class InvalidAPIKeyError(AIProviderError):
    """Raised when the API key is invalid or missing."""


class ModelUnavailableError(AIProviderError):
    """Raised when the requested model is not available."""


class EmbeddingFailureError(AIProviderError):
    """Raised when embedding generation fails."""


class RetryExhaustedError(AIProviderError):
    """Raised after all retry attempts are exhausted."""


class ImageUnreadableError(AIProviderError):
    """Raised when a provider cannot process an image input."""
