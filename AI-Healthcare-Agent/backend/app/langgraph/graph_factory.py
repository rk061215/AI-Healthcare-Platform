from __future__ import annotations

from typing import Any, Optional

from app.langgraph.config import LangGraphConfig
from app.langgraph.exceptions import GraphNotFoundError
from app.langgraph.graph_context import GraphContext
from app.langgraph.graph_registry import get_global_registry
from app.langgraph.graph_runtime import BaseGraph
from app.langgraph.graph_state import GraphState


class GraphFactory:
    @staticmethod
    def create(
        graph_name: str,
        config: Optional[LangGraphConfig] = None,
        state: Optional[GraphState] = None,
        context: Optional[GraphContext] = None,
    ) -> BaseGraph:
        registry = get_global_registry()
        graph_class = registry.get(graph_name)
        resolved_config = config or LangGraphConfig(graph_name=graph_name)
        resolved_state = state or GraphState(graph_name=graph_name)
        resolved_context = context or GraphContext(
            config=resolved_config,
            state=resolved_state,
        )
        return graph_class(
            config=resolved_config,
            state=resolved_state,
            context=resolved_context,
        )

    @staticmethod
    def create_or_none(
        graph_name: str,
        config: Optional[LangGraphConfig] = None,
        state: Optional[GraphState] = None,
        context: Optional[GraphContext] = None,
    ) -> Optional[BaseGraph]:
        try:
            return GraphFactory.create(
                graph_name=graph_name,
                config=config,
                state=state,
                context=context,
            )
        except GraphNotFoundError:
            return None
