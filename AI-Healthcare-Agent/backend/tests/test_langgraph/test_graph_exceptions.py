from __future__ import annotations

import pytest

from app.langgraph.exceptions import (
    GraphExecutionError,
    GraphNotFoundError,
    GraphTimeoutError,
    InvalidGraphDefinitionError,
    NodeExecutionError,
    NodeTimeoutError,
)


class TestGraphExceptions:
    def test_graph_not_found(self):
        exc = GraphNotFoundError("test graph not found")
        assert "test graph not found" in str(exc)

    def test_graph_timeout(self):
        exc = GraphTimeoutError("Graph exceeded timeout")
        assert "Graph exceeded timeout" in str(exc)

    def test_graph_execution(self):
        exc = GraphExecutionError("Execution failed")
        assert "Execution failed" in str(exc)

    def test_node_execution(self):
        exc = NodeExecutionError("Node 'foo' failed")
        assert "Node 'foo' failed" in str(exc)

    def test_node_timeout(self):
        exc = NodeTimeoutError("Node 'bar' exceeded 30000ms timeout")
        assert "Node 'bar' exceeded 30000ms timeout" in str(exc)

    def test_invalid_graph_definition(self):
        exc = InvalidGraphDefinitionError("Graph 'x' is already registered")
        assert "Graph 'x' is already registered" in str(exc)

    def test_exception_inheritance(self):
        assert issubclass(GraphNotFoundError, Exception)
        assert issubclass(GraphTimeoutError, Exception)
        assert issubclass(GraphExecutionError, Exception)
        assert issubclass(NodeExecutionError, Exception)
        assert issubclass(NodeTimeoutError, Exception)
        assert issubclass(InvalidGraphDefinitionError, Exception)
