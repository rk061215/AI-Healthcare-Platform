from __future__ import annotations

from typing import Optional

from app.tools.base_tool import BaseTool
from app.tools.config import ToolConfig
from app.tools.exceptions import ToolNotFoundError
from app.tools.tool_registry import get_global_registry


class ToolFactory:
    @staticmethod
    def create(tool_type: str, config: Optional[ToolConfig] = None) -> BaseTool:
        registry = get_global_registry()
        tool_class = registry.get(tool_type)
        return tool_class(config=config)

    @staticmethod
    def create_or_none(tool_type: str, config: Optional[ToolConfig] = None) -> Optional[BaseTool]:
        try:
            return ToolFactory.create(tool_type, config=config)
        except ToolNotFoundError:
            return None
