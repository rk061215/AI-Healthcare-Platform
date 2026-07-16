from __future__ import annotations

from typing import Optional, Type

from app.langgraph.exceptions import GraphNotFoundError, InvalidGraphDefinitionError
from app.langgraph.graph_runtime import BaseGraph


class GraphRegistry:
    def __init__(self) -> None:
        self._graphs: dict[str, type[BaseGraph]] = {}

    def register(self, name: str, graph_class: type[BaseGraph]) -> None:
        if not issubclass(graph_class, BaseGraph):
            raise InvalidGraphDefinitionError(
                f"'{graph_class.__name__}' must extend BaseGraph"
            )
        if name in self._graphs:
            raise InvalidGraphDefinitionError(f"Graph '{name}' is already registered")
        self._graphs[name] = graph_class

    def unregister(self, name: str) -> None:
        self._graphs.pop(name, None)

    def get(self, name: str) -> type[BaseGraph]:
        graph = self._graphs.get(name)
        if graph is None:
            raise GraphNotFoundError(f"Graph '{name}' is not registered")
        return graph

    def list_graphs(self) -> list[str]:
        return list(self._graphs.keys())

    def clear(self) -> None:
        self._graphs.clear()


_global_registry: Optional[GraphRegistry] = None


def get_global_registry() -> GraphRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = GraphRegistry()
    return _global_registry
