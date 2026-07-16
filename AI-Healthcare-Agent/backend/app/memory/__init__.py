"""Memory Framework for the AI Healthcare Follow-up Assistant.

Provides a provider-independent, privacy-aware memory system for AI agents.
Supports multiple memory types (conversation, document context, patient context,
preference, tool), pluggable storage backends, and configurable policies
(retention, privacy, expiry).

Usage:
    from app.memory import MemoryService, MemoryConfig
    service = MemoryService()
    entry = service.extract_from_chat(
        session_id="sess_001",
        query="What medications?",
        answer="The patient takes metformin.",
        turn_number=1,
    )
    memories = service.recall(session_id="sess_001", memory_type="conversation")
"""

from app.memory.config import MemoryConfig
from app.memory.exceptions import (
    ExpiryPolicyViolationError,
    MemoryError,
    MemoryExpiredError,
    MemoryExtractionError,
    MemoryFullError,
    MemoryNotFoundError,
    MemoryPruningError,
    MemoryRetrievalError,
    MemoryStoreError,
    MemorySummarizationError,
    MemoryTypeError,
    PolicyViolationError,
    PrivacyPolicyViolationError,
    RetentionPolicyViolationError,
    SessionNotFoundError,
)
from app.memory.memory_factory import MemoryFactory
from app.memory.memory_registry import MemoryRegistry, get_global_registry
from app.memory.memory_service import MemoryService
from app.memory.models import (
    MEMORY_SCHEMA_VERSION,
    ConversationMemoryData,
    DocumentContextData,
    MemoryEntry,
    MemoryImportance,
    MemoryQuery,
    MemorySummary,
    MemoryType,
    PatientContextData,
    PreferenceMemoryData,
    ToolMemoryData,
)
from app.memory.policies.expiry_policy import ExpiryPolicy
from app.memory.policies.privacy_policy import PrivacyPolicy
from app.memory.policies.retention_policy import RetentionPolicy
from app.memory.processors.memory_extractor import MemoryExtractor
from app.memory.processors.memory_pruner import MemoryPruner, PruningReport
from app.memory.processors.memory_retriever import MemoryRetriever
from app.memory.processors.memory_summarizer import MemorySummarizer, SummarizationResult
from app.memory.stores.in_memory_store import InMemoryStore
from app.memory.types.conversation_memory import ConversationMemory
from app.memory.types.document_context import DocumentContext
from app.memory.types.patient_context import PatientContext
from app.memory.types.preference_memory import PreferenceMemory
from app.memory.types.tool_memory import ToolMemory


get_global_registry().register("in_memory", InMemoryStore)


__all__ = [
    "MemoryConfig",
    "MemoryService",
    "MemoryFactory",
    "MemoryRegistry",
    "get_global_registry",
    "MemoryEntry",
    "MemoryType",
    "MemoryImportance",
    "MemoryQuery",
    "MemorySummary",
    "ConversationMemoryData",
    "DocumentContextData",
    "PatientContextData",
    "PreferenceMemoryData",
    "ToolMemoryData",
    "MEMORY_SCHEMA_VERSION",
    "InMemoryStore",
    "ConversationMemory",
    "DocumentContext",
    "PatientContext",
    "PreferenceMemory",
    "ToolMemory",
    "MemoryExtractor",
    "MemoryRetriever",
    "MemorySummarizer",
    "SummarizationResult",
    "MemoryPruner",
    "PruningReport",
    "RetentionPolicy",
    "PrivacyPolicy",
    "ExpiryPolicy",
    "MemoryError",
    "MemoryStoreError",
    "MemoryNotFoundError",
    "MemoryTypeError",
    "MemoryFullError",
    "MemoryExpiredError",
    "MemoryExtractionError",
    "MemoryRetrievalError",
    "MemorySummarizationError",
    "MemoryPruningError",
    "PolicyViolationError",
    "RetentionPolicyViolationError",
    "PrivacyPolicyViolationError",
    "ExpiryPolicyViolationError",
    "SessionNotFoundError",
]
