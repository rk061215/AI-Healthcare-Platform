from __future__ import annotations

import pytest

from app.langgraph.exceptions import GraphNotFoundError, InvalidGraphDefinitionError
from app.langgraph.graph_registry import GraphRegistry, get_global_registry
from app.langgraph.graph_runtime import BaseGraph
from app.langgraph.graph_state import GraphState


class StubGraph(BaseGraph):
    def build(self) -> None:
        pass

    def _run_pipeline(self, state: GraphState) -> GraphState:
        return state


class TestGraphRegistry:
    def test_register_and_get(self):
        registry = GraphRegistry()
        registry.register("test_graph", StubGraph)
        retrieved = registry.get("test_graph")
        assert retrieved is StubGraph

    def test_get_nonexistent(self):
        registry = GraphRegistry()
        with pytest.raises(GraphNotFoundError):
            registry.get("nonexistent")

    def test_register_duplicate(self):
        registry = GraphRegistry()
        registry.register("dup", StubGraph)
        with pytest.raises(InvalidGraphDefinitionError):
            registry.register("dup", StubGraph)

    def test_unregister(self):
        registry = GraphRegistry()
        registry.register("g1", StubGraph)
        registry.unregister("g1")
        with pytest.raises(GraphNotFoundError):
            registry.get("g1")

    def test_list_graphs(self):
        registry = GraphRegistry()
        registry.register("a", StubGraph)
        registry.register("b", StubGraph)
        names = registry.list_graphs()
        assert "a" in names
        assert "b" in names
        assert len(names) == 2

    def test_clear(self):
        registry = GraphRegistry()
        registry.register("a", StubGraph)
        registry.clear()
        assert registry.list_graphs() == []

    def test_global_registry_is_singleton(self):
        r1 = get_global_registry()
        r2 = get_global_registry()
        assert r1 is r2
