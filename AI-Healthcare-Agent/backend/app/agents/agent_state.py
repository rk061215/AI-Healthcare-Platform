from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class AgentPhase(str, Enum):
    IDLE = "idle"
    INITIALIZING = "initializing"
    CHECKING_HANDLER = "checking_handler"
    PREPARING_CONTEXT = "preparing_context"
    RETRIEVING_MEMORY = "retrieving_memory"
    RETRIEVING_DOCUMENTS = "retrieving_documents"
    INVOKING_RAG = "invoking_rag"
    INVOKING_TOOLS = "invoking_tools"
    POST_PROCESSING = "post_processing"
    VALIDATING = "validating"
    CLEANING_UP = "cleaning_up"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


@dataclass
class ComponentTrace:
    component: str
    status: ExecutionStatus
    duration_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class AgentState:
    session_id: str
    phase: AgentPhase = AgentPhase.IDLE
    status: ExecutionStatus = ExecutionStatus.PENDING
    invoked_components: list[ComponentTrace] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    total_duration_ms: float = 0.0
    token_usage: dict[str, int] = field(default_factory=dict)
    trace_id: str = ""
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def start(self, trace_id: str) -> None:
        import time
        self.trace_id = trace_id
        self.phase = AgentPhase.INITIALIZING
        self.status = ExecutionStatus.RUNNING
        self.start_time = time.time()

    def complete(self) -> None:
        import time
        self.phase = AgentPhase.COMPLETED
        self.status = ExecutionStatus.SUCCESS
        self.end_time = time.time()
        self.total_duration_ms = (self.end_time - self.start_time) * 1000

    def fail(self, error: str) -> None:
        import time
        self.phase = AgentPhase.FAILED
        self.status = ExecutionStatus.FAILURE
        self.end_time = time.time()
        self.total_duration_ms = (self.end_time - self.start_time) * 1000
        self.errors.append(error)

    def add_component_trace(
        self, component: str, status: ExecutionStatus,
        duration_ms: float = 0.0, error: Optional[str] = None,
    ) -> None:
        self.invoked_components.append(
            ComponentTrace(component=component, status=status, duration_ms=duration_ms, error=error)
        )

    def add_error(self, error: str) -> None:
        self.errors.append(error)

    def set_phase(self, phase: AgentPhase) -> None:
        self.phase = phase

    def increment_retry(self) -> int:
        self.retry_count += 1
        return self.retry_count
