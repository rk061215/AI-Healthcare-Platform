from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.langgraph.config import LangGraphConfig
from app.langgraph.exceptions import GraphExecutionError, GraphTimeoutError
from app.langgraph.graph_checkpoint import CheckpointManager
from app.langgraph.graph_context import GraphContext
from app.langgraph.graph_events import EventBus, GraphEvent, GraphEventType
from app.langgraph.graph_executor import GraphExecutor
from app.langgraph.graph_metrics import MetricsCollector
from app.langgraph.graph_state import GraphPhase, GraphState, GraphStatus


class BaseGraph(ABC):
    def __init__(
        self,
        config: Optional[LangGraphConfig] = None,
        state: Optional[GraphState] = None,
        context: Optional[GraphContext] = None,
    ) -> None:
        self._config = config or LangGraphConfig()
        self._state = state or GraphState(graph_name=self._config.graph_name)
        self._context = context or GraphContext(config=self._config, state=self._state)
        self._event_bus = EventBus() if self._config.enable_events else EventBus()
        self._metrics = (
            MetricsCollector(
                graph_name=self._config.graph_name,
                session_id=self._state.session_id,
            )
            if self._config.enable_metrics
            else None
        )
        self._checkpoint_mgr = (
            CheckpointManager() if self._config.enable_checkpointing else None
        )
        self._executor = GraphExecutor(
            event_bus=self._event_bus,
            metrics_collector=self._metrics,
            node_timeout_ms=self._config.node_timeout_ms,
            max_retries=self._config.max_retries,
            retry_delay=self._config.retry_delay_seconds,
        )
        self._started_at: float = 0.0
        self._built = False

    @property
    def config(self) -> LangGraphConfig:
        return self._config

    @property
    def state(self) -> GraphState:
        return self._state

    @property
    def context(self) -> GraphContext:
        return self._context

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def executor(self) -> GraphExecutor:
        return self._executor

    @property
    def metrics(self) -> Optional[MetricsCollector]:
        return self._metrics

    @abstractmethod
    def build(self) -> None:
        ...

    def initialize(self) -> None:
        if not self._built:
            self.build()
            self._built = True

    def execute(self, state: Optional[GraphState] = None) -> GraphState:
        self.initialize()
        if state is not None:
            self._state = state

        self._started_at = time.perf_counter()
        self._state.status = GraphStatus.RUNNING.value
        self._state.phase = GraphPhase.START.value

        self._event_bus.emit(GraphEvent(
            event_type=GraphEventType.GRAPH_STARTED,
            graph_name=self._config.graph_name,
            session_id=self._state.session_id,
            data={"query": self._state.query},
        ))

        try:
            result = self._run_pipeline(self._state)
            elapsed = (time.perf_counter() - self._started_at) * 1000
            if elapsed > self._config.execution_timeout_ms:
                raise GraphTimeoutError(
                    f"Graph exceeded {self._config.execution_timeout_ms}ms timeout"
                )
            result.total_duration_ms = elapsed
            result.status = GraphStatus.COMPLETED.value
            result.phase = GraphPhase.COMPLETED.value

            self._event_bus.emit(GraphEvent(
                event_type=GraphEventType.GRAPH_COMPLETED,
                graph_name=self._config.graph_name,
                session_id=result.session_id,
                data={"total_duration_ms": elapsed, "response": result.final_response},
            ))

            if self._checkpoint_mgr:
                self._checkpoint_mgr.create_checkpoint(result.snapshot())

            return result

        except Exception as exc:
            elapsed = (time.perf_counter() - self._started_at) * 1000
            self._state.status = GraphStatus.FAILED.value
            self._state.phase = GraphPhase.FAILED.value
            self._state.total_duration_ms = elapsed
            self._state.errors.append(str(exc))

            if self._metrics:
                self._metrics.increment_errors()

            self._event_bus.emit(GraphEvent(
                event_type=GraphEventType.GRAPH_FAILED,
                graph_name=self._config.graph_name,
                session_id=self._state.session_id,
                error=str(exc),
            ))

            raise GraphExecutionError(str(exc)) from exc

    @abstractmethod
    def _run_pipeline(self, state: GraphState) -> GraphState:
        ...

    def resume(self, state: GraphState) -> GraphState:
        self._state = state
        self._state.status = GraphStatus.RUNNING.value
        return self.execute(self._state)

    def checkpoint(self) -> Optional[str]:
        if self._checkpoint_mgr:
            return self._checkpoint_mgr.create_checkpoint(self._state.snapshot())
        return None

    def shutdown(self) -> None:
        self._event_bus.clear()
        if self._metrics:
            snapshot = self._metrics.snapshot(
                status=self._state.status,
            )
