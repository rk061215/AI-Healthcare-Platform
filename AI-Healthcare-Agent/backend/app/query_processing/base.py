from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.query_processing.config import QueryUnderstandingConfig
from app.query_processing.models import UnderstandingResult


class BaseQueryUnderstander(ABC):
    def __init__(self, config: Optional[QueryUnderstandingConfig] = None):
        self._config = config or QueryUnderstandingConfig()

    @property
    def config(self) -> QueryUnderstandingConfig:
        return self._config

    @abstractmethod
    def understand(self, query: str, context: Optional[str] = None) -> UnderstandingResult:
        """Analyze and understand a user's medical query.

        Args:
            query: The raw user query string.
            context: Optional conversation or patient context.

        Returns:
            UnderstandingResult with intent, entities, sub-questions, and metadata.
        """

    @abstractmethod
    def extract_entities(self, query: str) -> list[dict]:
        """Extract medical entities from a query without full understanding.

        Args:
            query: The query string.

        Returns:
            A list of extracted entity dicts with type, value, and position.
        """

    @abstractmethod
    def decompose(self, query: str) -> list[dict]:
        """Decompose a compound medical question into sub-questions.

        Args:
            query: The query string.

        Returns:
            A list of sub-question dicts with text, intent, and weight.
        """
