from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class GraphPhase(Enum):
    START = "start"
    MEMORY_LOAD = "memory_load"
    QA_GENERATION = "qa_generation"
    TOOL_SELECTION = "tool_selection"
    TOOL_EXECUTION = "tool_execution"
    RETRIEVAL = "retrieval"
    CONTEXT_BUILDING = "context_building"
    RESPONSE_GENERATION = "response_generation"
    MEMORY_PERSIST = "memory_persist"
    COMPLETED = "completed"
    FAILED = "failed"


class GraphStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class NodeMetricsEntry:
    node_name: str
    phase: str
    duration_ms: float = 0.0
    status: str = "pending"
    error: Optional[str] = None
    token_usage: dict[str, int] = field(default_factory=dict)


@dataclass
class ExecutionTrace:
    node_name: str
    phase: str
    started_at: float = 0.0
    completed_at: float = 0.0
    duration_ms: float = 0.0
    status: str = "unknown"
    error: Optional[str] = None


@dataclass
class GraphState:
    user_id: str = ""
    session_id: str = ""
    request_id: str = ""
    query: str = ""
    rewritten_query: str = ""
    conversation_history: str = ""
    retrieved_documents: list[dict[str, Any]] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    memory_context: list[dict[str, Any]] = field(default_factory=list)
    final_response: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    latency_metrics: dict[str, float] = field(default_factory=dict)
    execution_trace: list[ExecutionTrace] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    graph_name: str = "medical_qa"
    phase: str = GraphPhase.START.value
    status: str = GraphStatus.PENDING.value
    current_node: str = ""
    node_metrics: dict[str, NodeMetricsEntry] = field(default_factory=dict)
    requires_tool: bool = False
    requires_retrieval: bool = True
    patient_id: str = ""
    report_id: Optional[str] = None
    document_id: Optional[str] = None
    document_type: Optional[str] = None
    document_sections: list[str] = field(default_factory=list)
    language: str = "en"
    tool_type: Optional[str] = None
    tool_action: Optional[str] = None
    total_duration_ms: float = 0.0
    token_usage: dict[str, int] = field(default_factory=dict)
    checkpoint_id: Optional[str] = None
    need_tool: bool = False
    need_retrieval: bool = True
    memory_entries: list[dict[str, Any]] = field(default_factory=list)
    agent_response: dict[str, Any] = field(default_factory=dict)
    tool_decision: dict[str, Any] = field(default_factory=dict)
    tool_result: dict[str, Any] = field(default_factory=dict)
    rag_response: dict[str, Any] = field(default_factory=dict)
    retrieved_evidence: list[dict[str, Any]] = field(default_factory=list)
    built_context: str = ""
    response_metadata: dict[str, Any] = field(default_factory=dict)
    persisted_memory_id: str = ""
    services: dict[str, Any] = field(default_factory=dict)
    context_updates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "query": self.query,
            "phase": self.phase,
            "status": self.status,
            "current_node": self.current_node,
            "final_response": self.final_response,
            "errors": self.errors,
            "total_duration_ms": self.total_duration_ms,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith("_")
        }
