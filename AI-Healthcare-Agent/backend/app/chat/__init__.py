"""Medical Document QA Agent — first user-facing AI capability.

Session-based question answering over uploaded medical documents.
Coordinates the RAG Engine with confidence scoring, question suggestions,
response formatting, and lightweight session management.

No persistent memory, no LangGraph, no multi-agent orchestration.
"""

from app.chat.chat_service import ChatService
from app.chat.chat_session import SessionManager
from app.chat.config import ChatConfig
from app.chat.confidence import ConfidenceCalculator
from app.chat.exceptions import (
    ChatError,
    ConfidenceCalculationError,
    EmptyQuestionError,
    MaxQuestionsExceededError,
    NoDocumentInSessionError,
    QuestionGenerationError,
    SessionExpiredError,
    SessionNotFoundError,
)
from app.chat.models import (
    CHAT_SCHEMA_VERSION,
    ChatRequest,
    ChatResponse,
    ChatSession,
    ConfidenceLevel,
    ConfidenceScore,
    DocumentSummary,
    QAPair,
    QuestionType,
    SuggestedQuestion,
)
from app.chat.question_suggester import QuestionSuggester
from app.chat.response_formatter import ResponseFormatter

__all__ = [
    "ChatService",
    "SessionManager",
    "ChatConfig",
    "ConfidenceCalculator",
    "QuestionSuggester",
    "ResponseFormatter",
    "ChatRequest",
    "ChatResponse",
    "ChatSession",
    "QAPair",
    "ConfidenceScore",
    "ConfidenceLevel",
    "SuggestedQuestion",
    "QuestionType",
    "DocumentSummary",
    "CHAT_SCHEMA_VERSION",
    "ChatError",
    "SessionNotFoundError",
    "SessionExpiredError",
    "NoDocumentInSessionError",
    "QuestionGenerationError",
    "ConfidenceCalculationError",
    "EmptyQuestionError",
    "MaxQuestionsExceededError",
]
