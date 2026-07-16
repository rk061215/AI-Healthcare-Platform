from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricsSnapshot:
    graph_name: str
    session_id: str
    total_duration_ms: float = 0.0
    node_count: int = 0
    node_durations: dict[str, float] = field(default_factory=dict)
    memory_latency_ms: float = 0.0
    retrieval_latency_ms: float = 0.0
    tool_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0
    token_usage: dict[str, int] = field(default_factory=dict)
    status: str = "unknown"
    error_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_name": self.graph_name,
            "session_id": self.session_id,
            "total_duration_ms": self.total_duration_ms,
            "node_count": self.node_count,
            "node_durations": dict(self.node_durations),
            "memory_latency_ms": self.memory_latency_ms,
            "retrieval_latency_ms": self.retrieval_latency_ms,
            "tool_latency_ms": self.tool_latency_ms,
            "generation_latency_ms": self.generation_latency_ms,
            "token_usage": dict(self.token_usage),
            "status": self.status,
            "error_count": self.error_count,
        }


class MetricsCollector:
    def __init__(self, graph_name: str = "", session_id: str = "") -> None:
        self._graph_name = graph_name
        self._session_id = session_id
        self._start_time = time.perf_counter()
        self._node_times: dict[str, float] = {}
        self._node_starts: dict[str, float] = {}
        self._memory_ms: float = 0.0
        self._retrieval_ms: float = 0.0
        self._tool_ms: float = 0.0
        self._generation_ms: float = 0.0
        self._token_usage: dict[str, int] = {}
        self._error_count: int = 0

    def start_node(self, node_name: str) -> None:
        self._node_starts[node_name] = time.perf_counter()

    def end_node(self, node_name: str) -> float:
        elapsed = (time.perf_counter() - self._node_starts.get(node_name, 0)) * 1000
        self._node_times[node_name] = elapsed
        return elapsed

    def record_memory_latency(self, ms: float) -> None:
        self._memory_ms = ms

    def record_retrieval_latency(self, ms: float) -> None:
        self._retrieval_ms = ms

    def record_tool_latency(self, ms: float) -> None:
        self._tool_ms = ms

    def record_generation_latency(self, ms: float) -> None:
        self._generation_ms = ms

    def record_token_usage(self, tokens: dict[str, int]) -> None:
        for k, v in tokens.items():
            self._token_usage[k] = self._token_usage.get(k, 0) + v

    def increment_errors(self) -> None:
        self._error_count += 1

    def snapshot(self, status: str = "unknown") -> MetricsSnapshot:
        return MetricsSnapshot(
            graph_name=self._graph_name,
            session_id=self._session_id,
            total_duration_ms=(time.perf_counter() - self._start_time) * 1000,
            node_count=len(self._node_times),
            node_durations=dict(self._node_times),
            memory_latency_ms=self._memory_ms,
            retrieval_latency_ms=self._retrieval_ms,
            tool_latency_ms=self._tool_ms,
            generation_latency_ms=self._generation_ms,
            token_usage=dict(self._token_usage),
            status=status,
            error_count=self._error_count,
        )
