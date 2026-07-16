from __future__ import annotations


class AgentError(Exception):
    """Base exception for all agent module errors."""


class AgentNotFoundError(AgentError):
    """Raised when an agent type is not registered."""


class AgentRegistrationError(AgentError):
    """Raised when agent registration fails (e.g. duplicate)."""


class AgentInitializationError(AgentError):
    """Raised when an agent fails to initialize."""


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""


class AgentContextError(AgentError):
    """Raised when the agent context is invalid or missing."""


class AgentStateError(AgentError):
    """Raised when an invalid state transition occurs."""


class AgentTimeoutError(AgentError):
    """Raised when agent execution exceeds the configured timeout."""


class AgentValidationError(AgentError):
    """Raised when the agent response fails validation."""


class AgentRetryExhaustedError(AgentError):
    """Raised when all retry attempts are exhausted."""


class AgentMemoryError(AgentError):
    """Raised when memory operations fail during agent execution."""


class AgentRAGError(AgentError):
    """Raised when RAG operations fail during agent execution."""


class AgentToolError(AgentError):
    """Raised when tool invocation fails during agent execution."""


class AgentResponseError(AgentError):
    """Raised when response formatting or processing fails."""
