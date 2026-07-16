from __future__ import annotations


class ChatError(Exception):
    """Base exception for all chat module errors."""


class SessionNotFoundError(ChatError):
    """Raised when a session ID does not exist."""


class SessionExpiredError(ChatError):
    """Raised when a session has expired due to inactivity."""


class NoDocumentInSessionError(ChatError):
    """Raised when an operation requires a document but none is associated."""


class QuestionGenerationError(ChatError):
    """Raised when question suggestion generation fails."""


class ConfidenceCalculationError(ChatError):
    """Raised when confidence scoring encounters an error."""


class EmptyQuestionError(ChatError):
    """Raised when the user submits an empty question."""


class MaxQuestionsExceededError(ChatError):
    """Raised when the session has reached the maximum question limit."""
