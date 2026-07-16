from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional

from app.ai.config import AIProviderConfig
from app.ai.exceptions import (
    AIProviderError,
    EmbeddingFailureError,
    InvalidAPIKeyError,
    ModelUnavailableError,
    QuotaExceededError,
    RetryExhaustedError,
    TimeoutError,
)


class BaseProvider(ABC):
    name: str = "base"
    config: AIProviderConfig

    def __init__(self, config: Optional[AIProviderConfig] = None):
        self.config = config or AIProviderConfig()

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the provider client, validate credentials, and check model availability."""

    @abstractmethod
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text from a prompt. Returns the response as a string."""

    @abstractmethod
    def generate_structured_output(
        self, prompt: str, output_schema: dict, system_prompt: Optional[str] = None
    ) -> dict:
        """Generate structured JSON output matching the provided schema."""

    @abstractmethod
    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""

    @abstractmethod
    def stream_response(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """Stream a response token by token."""

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""

    @abstractmethod
    def health_check(self) -> dict:
        """Check provider health. Returns dict with status and optional error."""

    @abstractmethod
    def close(self) -> None:
        """Close the provider client and release resources."""
