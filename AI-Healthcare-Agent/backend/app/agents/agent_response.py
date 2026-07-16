from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from app.agents.agent_state import ExecutionStatus


@dataclass
class AgentResponse:
    success: bool
    answer: str = ""
    data: Any = None
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    error: Optional[str] = None
    session_id: str = ""
    trace_id: str = ""
    total_duration_ms: float = 0.0
    token_usage: dict[str, int] = field(default_factory=dict)
    citations: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(
        cls, answer: str = "", data: Any = None,
        session_id: str = "", trace_id: str = "",
        total_duration_ms: float = 0.0,
        token_usage: dict[str, int] | None = None,
        citations: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AgentResponse:
        return cls(
            success=True,
            answer=answer,
            data=data,
            status=ExecutionStatus.SUCCESS,
            session_id=session_id,
            trace_id=trace_id,
            total_duration_ms=total_duration_ms,
            token_usage=token_usage or {},
            citations=citations or [],
            metadata=metadata or {},
        )

    @classmethod
    def error(
        cls, error: str, session_id: str = "",
        trace_id: str = "", total_duration_ms: float = 0.0,
    ) -> AgentResponse:
        return cls(
            success=False,
            answer="",
            status=ExecutionStatus.FAILURE,
            error=error,
            session_id=session_id,
            trace_id=trace_id,
            total_duration_ms=total_duration_ms,
        )
