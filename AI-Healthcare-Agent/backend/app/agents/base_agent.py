from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.agents.agent_context import AgentContext
from app.agents.agent_response import AgentResponse
from app.agents.config import AgentConfig


class BaseAgent(ABC):
    def __init__(self, config: Optional[AgentConfig] = None) -> None:
        self._config = config or AgentConfig()

    @property
    def config(self) -> AgentConfig:
        return self._config

    @abstractmethod
    def initialize(self) -> None:
        """Prepare internal resources once before any execution."""

    @abstractmethod
    def can_handle(self, context: AgentContext) -> bool:
        """Return True if this agent can handle the given context."""

    @abstractmethod
    def prepare_context(self, context: AgentContext) -> AgentContext:
        """Augment or transform the context before processing."""

    @abstractmethod
    def retrieve_memory(self, context: AgentContext) -> AgentContext:
        """Load relevant memory entries into context."""

    @abstractmethod
    def retrieve_documents(self, context: AgentContext) -> AgentContext:
        """Load relevant document evidence into context."""

    @abstractmethod
    def invoke_rag(self, context: AgentContext) -> AgentResponse:
        """Execute the RAG pipeline and return a response."""

    def invoke_tools(self, context: AgentContext) -> AgentContext:
        """Placeholder: invoke external tools (no-op by default)."""
        return context

    @abstractmethod
    def post_process(self, response: AgentResponse, context: AgentContext) -> AgentResponse:
        """Transform or enrich the raw response."""

    @abstractmethod
    def validate_response(self, response: AgentResponse) -> AgentResponse:
        """Validate the final response before returning to the caller."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release resources after execution completes."""
