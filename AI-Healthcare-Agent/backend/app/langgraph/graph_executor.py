from __future__ import annotations

import time
from typing import Any, Callable, Optional

from app.langgraph.exceptions import (
    NodeExecutionError,
    NodeTimeoutError,
)
from app.langgraph.graph_events import EventBus, GraphEvent, GraphEventType
from app.langgraph.graph_metrics import MetricsCollector
from app.langgraph.graph_state import (
    ExecutionTrace,
    GraphPhase,
    GraphState,
    GraphStatus,
    NodeMetricsEntry,
)


class GraphExecutor:
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        metrics_collector: Optional[MetricsCollector] = None,
        node_timeout_ms: float = 30000.0,
        max_retries: int = 2,
        retry_delay: float = 0.5,
    ) -> None:
        self._event_bus = event_bus or EventBus()
        self._metrics = metrics_collector
        self._node_timeout_ms = node_timeout_ms
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._nodes: dict[str, Callable] = {}
        self._conditional_edges: dict[str, Callable] = {}

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def metrics(self) -> Optional[MetricsCollector]:
        return self._metrics

    def register_node(self, name: str, fn: Callable) -> None:
        self._nodes[name] = fn

    def register_conditional_edge(self, name: str, fn: Callable) -> None:
        self._conditional_edges[name] = fn

    def execute_node(
        self,
        node_name: str,
        state: GraphState,
        phase: str,
    ) -> GraphState:
        if node_name not in self._nodes:
            raise NodeExecutionError(f"Node '{node_name}' is not registered")

        state.current_node = node_name
        state.phase = phase

        if self._metrics:
            self._metrics.start_node(node_name)

        self._event_bus.emit(GraphEvent(
            event_type=GraphEventType.NODE_STARTED,
            graph_name=state.graph_name,
            session_id=state.session_id,
            node_name=node_name,
        ))

        trace = ExecutionTrace(
            node_name=node_name,
            phase=phase,
            started_at=time.time(),
            status="running",
        )

        try:
            result = self._run_with_timeout(node_name, state)
            trace.completed_at = time.time()
            trace.duration_ms = (trace.completed_at - trace.started_at) * 1000
            trace.status = "completed"
            state.execution_trace.append(trace)
            entry = NodeMetricsEntry(
                node_name=node_name,
                phase=phase,
                duration_ms=trace.duration_ms,
                status="completed",
            )
            state.node_metrics[node_name] = entry
            state.latency_metrics[node_name] = trace.duration_ms

            if self._metrics:
                self._metrics.end_node(node_name)

            self._event_bus.emit(GraphEvent(
                event_type=GraphEventType.NODE_COMPLETED,
                graph_name=state.graph_name,
                session_id=state.session_id,
                node_name=node_name,
                data={"duration_ms": trace.duration_ms},
            ))

            return result

        except Exception as exc:
            trace.completed_at = time.time()
            trace.duration_ms = (trace.completed_at - trace.started_at) * 1000
            trace.status = "failed"
            trace.error = str(exc)
            state.execution_trace.append(trace)
            state.errors.append(f"[{node_name}] {exc}")
            entry = NodeMetricsEntry(
                node_name=node_name,
                phase=phase,
                duration_ms=trace.duration_ms,
                status="failed",
                error=str(exc),
            )
            state.node_metrics[node_name] = entry
            state.latency_metrics[node_name] = trace.duration_ms
            state.status = GraphStatus.FAILED.value
            state.phase = GraphPhase.FAILED.value

            if self._metrics:
                self._metrics.end_node(node_name)
                self._metrics.increment_errors()

            self._event_bus.emit(GraphEvent(
                event_type=GraphEventType.NODE_FAILED,
                graph_name=state.graph_name,
                session_id=state.session_id,
                node_name=node_name,
                error=str(exc),
            ))

            raise NodeExecutionError(f"Node '{node_name}' failed: {exc}") from exc

    def evaluate_conditional(self, edge_name: str, state: GraphState) -> str:
        fn = self._conditional_edges.get(edge_name)
        if fn is None:
            raise NodeExecutionError(f"Conditional edge '{edge_name}' not found")
        return fn(state)

    def _run_with_timeout(self, node_name: str, state: GraphState) -> GraphState:
        fn = self._nodes[node_name]
        start = time.perf_counter()
        last_exc: Optional[Exception] = None

        for attempt in range(self._max_retries):
            try:
                result = fn(state)
                elapsed = (time.perf_counter() - start) * 1000
                if elapsed > self._node_timeout_ms:
                    raise NodeTimeoutError(
                        f"Node '{node_name}' exceeded {self._node_timeout_ms}ms timeout"
                    )
                return result
            except NodeTimeoutError:
                raise
            except Exception as exc:
                last_exc = exc
                if attempt < self._max_retries - 1:
                    time.sleep(self._retry_delay)
                continue

        raise NodeExecutionError(
            f"Node '{node_name}' failed after {self._max_retries} attempts: {last_exc}"
        ) from last_exc
