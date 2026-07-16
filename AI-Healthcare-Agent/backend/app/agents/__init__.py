"""Agent Framework — reusable abstractions for all future AI agents.

Provides BaseAgent lifecycle, AgentRegistry, AgentFactory, AgentExecutor,
AgentService, AgentContext, AgentState, AgentResponse, and the refactored
MedicalQAAgent. Designed to standardize agent interactions with Memory, RAG,
Tools, and future LangGraph orchestration.
"""

from app.agents.agent_context import AgentContext
from app.agents.agent_executor import AgentExecutor
from app.agents.agent_factory import AgentFactory
from app.agents.agent_registry import AgentRegistry, get_global_registry
from app.agents.agent_response import AgentResponse
from app.agents.agent_service import AgentService
from app.agents.agent_state import AgentPhase, AgentState, ComponentTrace, ExecutionStatus
from app.agents.agents.medical_qa_agent import MedicalQAAgent
from app.agents.base_agent import BaseAgent
from app.agents.config import AgentConfig
from app.agents.exceptions import (
    AgentContextError,
    AgentError,
    AgentExecutionError,
    AgentInitializationError,
    AgentMemoryError,
    AgentNotFoundError,
    AgentRAGError,
    AgentRegistrationError,
    AgentResponseError,
    AgentRetryExhaustedError,
    AgentStateError,
    AgentTimeoutError,
    AgentToolError,
    AgentValidationError,
)
from app.agents.orchestrator import AgentOrchestrator

_registry = get_global_registry()
_registry.register("medical_qa", MedicalQAAgent)

__all__ = [
    "BaseAgent",
    "AgentContext",
    "AgentState",
    "AgentPhase",
    "ExecutionStatus",
    "ComponentTrace",
    "AgentResponse",
    "AgentConfig",
    "AgentRegistry",
    "get_global_registry",
    "AgentFactory",
    "AgentExecutor",
    "AgentService",
    "MedicalQAAgent",
    "AgentOrchestrator",
    "AgentError",
    "AgentNotFoundError",
    "AgentRegistrationError",
    "AgentInitializationError",
    "AgentExecutionError",
    "AgentContextError",
    "AgentStateError",
    "AgentTimeoutError",
    "AgentValidationError",
    "AgentRetryExhaustedError",
    "AgentMemoryError",
    "AgentRAGError",
    "AgentToolError",
    "AgentResponseError",
]
