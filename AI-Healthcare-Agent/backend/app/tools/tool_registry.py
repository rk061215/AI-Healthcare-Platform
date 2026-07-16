from __future__ import annotations

from typing import Optional, Type

from app.tools.base_tool import BaseTool
from app.tools.exceptions import ToolNotFoundError, ToolRegistrationError


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, type[BaseTool]] = {}

    def register(self, name: str, tool_class: type[BaseTool]) -> None:
        if name in self._tools:
            raise ToolRegistrationError(f"Tool '{name}' is already registered")
        self._tools[name] = tool_class

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def get(self, name: str) -> type[BaseTool]:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolNotFoundError(f"Tool '{name}' is not registered")
        return tool

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def clear(self) -> None:
        self._tools.clear()


_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry
