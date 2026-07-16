from __future__ import annotations

import threading
from datetime import datetime, timezone

from app.langgraph.graph_events import EventBus, GraphEvent, GraphEventType


class TestGraphEvent:
    def test_event_creation(self):
        event = GraphEvent(
            event_type=GraphEventType.GRAPH_STARTED,
            graph_name="test",
            session_id="sess_1",
            node_name="load_memory",
            data={"key": "value"},
        )
        assert event.event_type == GraphEventType.GRAPH_STARTED
        assert event.graph_name == "test"
        assert event.session_id == "sess_1"
        assert event.node_name == "load_memory"
        assert event.data == {"key": "value"}
        assert isinstance(event.timestamp, datetime)

    def test_event_to_dict(self):
        event = GraphEvent(
            event_type=GraphEventType.NODE_COMPLETED,
            graph_name="test",
            session_id="sess_1",
            node_name="retriever",
            data={"duration_ms": 150.0},
        )
        d = event.to_dict()
        assert d["event_type"] == "node_completed"
        assert d["graph_name"] == "test"
        assert d["session_id"] == "sess_1"
        assert d["node_name"] == "retriever"
        assert d["data"]["duration_ms"] == 150.0
        assert "timestamp" in d
        assert d["error"] is None


class TestEventBus:
    def test_subscribe_and_emit(self):
        bus = EventBus()
        received = []

        def handler(event: GraphEvent) -> None:
            received.append(event)

        bus.subscribe(GraphEventType.GRAPH_STARTED, handler)

        event = GraphEvent(
            event_type=GraphEventType.GRAPH_STARTED,
            graph_name="test",
            session_id="sess_1",
        )
        bus.emit(event)
        assert len(received) == 1
        assert received[0].graph_name == "test"

    def test_unsubscribe(self):
        bus = EventBus()
        received = []

        def handler(event: GraphEvent) -> None:
            received.append(event)

        bus.subscribe(GraphEventType.NODE_STARTED, handler)
        bus.unsubscribe(GraphEventType.NODE_STARTED, handler)

        event = GraphEvent(
            event_type=GraphEventType.NODE_STARTED,
            graph_name="test",
            session_id="sess_1",
            node_name="test_node",
        )
        bus.emit(event)
        assert len(received) == 0

    def test_multiple_handlers(self):
        bus = EventBus()
        results = []

        def handler1(event: GraphEvent) -> None:
            results.append("h1")

        def handler2(event: GraphEvent) -> None:
            results.append("h2")

        bus.subscribe(GraphEventType.CHECKPOINT_CREATED, handler1)
        bus.subscribe(GraphEventType.CHECKPOINT_CREATED, handler2)

        event = GraphEvent(
            event_type=GraphEventType.CHECKPOINT_CREATED,
            graph_name="test",
            session_id="sess_1",
        )
        bus.emit(event)
        assert len(results) == 2

    def test_handler_exception_does_not_propagate(self):
        bus = EventBus()

        def failing_handler(event: GraphEvent) -> None:
            raise RuntimeError("handler failed")

        bus.subscribe(GraphEventType.GRAPH_STARTED, failing_handler)

        event = GraphEvent(
            event_type=GraphEventType.GRAPH_STARTED,
            graph_name="test",
            session_id="sess_1",
        )
        bus.emit(event)

    def test_clear(self):
        bus = EventBus()
        received = []

        def handler(event: GraphEvent) -> None:
            received.append(event)

        bus.subscribe(GraphEventType.GRAPH_COMPLETED, handler)
        bus.clear()
        bus.emit(GraphEvent(
            event_type=GraphEventType.GRAPH_COMPLETED,
            graph_name="test",
            session_id="sess_1",
        ))
        assert len(received) == 0

    def test_unrelated_events_not_delivered(self):
        bus = EventBus()
        received = []

        def handler(event: GraphEvent) -> None:
            received.append(event)

        bus.subscribe(GraphEventType.GRAPH_STARTED, handler)
        bus.emit(GraphEvent(
            event_type=GraphEventType.GRAPH_FAILED,
            graph_name="test",
            session_id="sess_1",
        ))
        assert len(received) == 0
