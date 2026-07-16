from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


class GraphEventType(Enum):
    GRAPH_STARTED = "graph_started"
    GRAPH_COMPLETED = "graph_completed"
    GRAPH_FAILED = "graph_failed"
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    NODE_FAILED = "node_failed"
    TOOL_EXECUTED = "tool_executed"
    MEMORY_RETRIEVED = "memory_retrieved"
    RETRIEVAL_COMPLETED = "retrieval_completed"
    RESPONSE_GENERATED = "response_generated"
    STATE_TRANSITION = "state_transition"
    CHECKPOINT_CREATED = "checkpoint_created"


@dataclass
class GraphEvent:
    event_type: GraphEventType
    graph_name: str
    session_id: str
    node_name: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "graph_name": self.graph_name,
            "session_id": self.session_id,
            "node_name": self.node_name,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }


EventHandler = Callable[[GraphEvent], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[GraphEventType, list[EventHandler]] = {}

    def subscribe(self, event_type: GraphEventType, handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: GraphEventType, handler: EventHandler) -> None:
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h is not handler
            ]

    def emit(self, event: GraphEvent) -> None:
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass

    def clear(self) -> None:
        self._handlers.clear()
