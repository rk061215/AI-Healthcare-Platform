from __future__ import annotations


class LangGraphError(Exception):
    """Base exception for all LangGraph runtime errors."""


class GraphNotFoundError(LangGraphError):
    """Raised when a graph is not found in the registry."""


class GraphExecutionError(LangGraphError):
    """Raised when a graph execution fails."""


class NodeExecutionError(LangGraphError):
    """Raised when a graph node fails to execute."""


class StateTransitionError(LangGraphError):
    """Raised on invalid state transitions."""


class CheckpointError(LangGraphError):
    """Raised when checkpoint operations fail."""


class NodeTimeoutError(LangGraphError):
    """Raised when a graph node exceeds its timeout."""


class GraphTimeoutError(LangGraphError):
    """Raised when the overall graph execution exceeds timeout."""


class InvalidGraphDefinitionError(LangGraphError):
    """Raised when a graph definition is invalid."""
