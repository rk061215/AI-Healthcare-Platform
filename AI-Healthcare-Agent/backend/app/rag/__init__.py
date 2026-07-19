"""RAG Engine — production-grade Retrieval-Augmented Generation orchestration.

Coordinates the complete RAG pipeline:
Query → Process → Classify → (Rewrite) → Retrieve → Build Context →
Guardrails (pre) → Generate → Guardrails (post) → Citations →
Structured RAG Response

Every stage is independently replaceable via dependency injection.
No Conversation Memory, no LangGraph, no Chat UI.
"""

from app.rag.citation_engine import CitationAnalysis, CitationEngine, CitationGroup, CitationScore
from app.rag.citation_manager import CitationManager
from app.rag.config import RAGEngineConfig
from app.rag.confidence_engine import ClaimConfidence, ConfidenceBreakdown, ConfidenceEngine, ConfidenceResult
from app.rag.exceptions import (
    CitationError,
    ConfigurationError,
    ContextBuildError,
    EmptyQueryError,
    GuardrailError,
    InsufficientContextError,
    QueryClassificationError,
    QueryError,
    RAGError,
    ResponseGenerationError,
    RetrievalError,
    UnsafeContentError,
    UnsupportedQueryError,
)
from app.rag.guardrails import Guardrails
from app.rag.models import (
    RAGMetrics,
    RAGRequest,
    RAGResponse,
    RAG_SCHEMA_VERSION,
)
from app.rag.query_classifier import QueryClassifier
from app.rag.query_processor import QueryProcessor
from app.rag.query_rewriter import BaseQueryRewriter, DefaultQueryRewriter
from app.rag.rag_engine import RAGEngine
from app.rag.response_generator import ResponseGenerator
from app.rag.retrieval_orchestrator import RetrievalOrchestrator

__all__ = [
    "RAGEngine",
    "RAGEngineConfig",
    "RAGRequest",
    "RAGResponse",
    "RAGMetrics",
    "RAG_SCHEMA_VERSION",
    "QueryProcessor",
    "QueryClassifier",
    "BaseQueryRewriter",
    "DefaultQueryRewriter",
    "RetrievalOrchestrator",
    "ResponseGenerator",
    "CitationManager",
    "CitationEngine",
    "CitationAnalysis",
    "CitationScore",
    "CitationGroup",
    "ConfidenceEngine",
    "ConfidenceResult",
    "ConfidenceBreakdown",
    "ClaimConfidence",
    "Guardrails",
    "RAGError",
    "ConfigurationError",
    "QueryError",
    "EmptyQueryError",
    "QueryClassificationError",
    "UnsupportedQueryError",
    "RetrievalError",
    "ContextBuildError",
    "InsufficientContextError",
    "ResponseGenerationError",
    "GuardrailError",
    "UnsafeContentError",
    "CitationError",
]
