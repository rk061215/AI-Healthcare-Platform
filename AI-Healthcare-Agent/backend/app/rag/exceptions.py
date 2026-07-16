from __future__ import annotations


class RAGError(Exception):
    """Base exception for all RAG engine errors."""


class ConfigurationError(RAGError):
    """Raised when RAG engine configuration is invalid."""


class QueryError(RAGError):
    """Raised when the query is invalid or cannot be processed."""


class QueryClassificationError(RAGError):
    """Raised when query classification fails."""


class RetrievalError(RAGError):
    """Raised when document retrieval fails."""


class ContextBuildError(RAGError):
    """Raised when context assembly fails."""


class InsufficientContextError(RAGError):
    """Raised when retrieved context is insufficient for a response."""


class CitationError(RAGError):
    """Raised when citation formatting or grounding fails."""


class GuardrailError(RAGError):
    """Raised when a guardrail check fails."""


class ResponseGenerationError(RAGError):
    """Raised when LLM response generation fails."""


class EmptyQueryError(QueryError):
    """Raised when the query is empty after preprocessing."""


class UnsafeContentError(GuardrailError):
    """Raised when guardrails detect unsafe or unsupported content."""


class UnsupportedQueryError(QueryClassificationError):
    """Raised when the query type is not supported for RAG."""
