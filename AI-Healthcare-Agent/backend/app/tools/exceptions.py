from __future__ import annotations


class ToolError(Exception):
    """Base exception for all tool module errors."""


class ToolNotFoundError(ToolError):
    """Raised when a tool type is not registered."""


class ToolRegistrationError(ToolError):
    """Raised when tool registration fails (e.g. duplicate)."""


class ToolValidationError(ToolError):
    """Raised when tool input validation fails."""


class ToolAuthorizationError(ToolError):
    """Raised when tool authorization check fails."""


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""


class ToolVerificationError(ToolError):
    """Raised when tool output verification fails."""


class ToolTimeoutError(ToolError):
    """Raised when tool execution exceeds the configured timeout."""


class ToolRetryExhaustedError(ToolError):
    """Raised when all retry attempts are exhausted."""


class ToolContextError(ToolError):
    """Raised when the tool context is invalid or missing."""


class ToolConfigError(ToolError):
    """Raised when the tool configuration is invalid."""


class ToolServiceError(ToolError):
    """Raised when the underlying service call fails."""


class ToolSelectorError(ToolError):
    """Raised when tool selection fails to find a matching tool."""
