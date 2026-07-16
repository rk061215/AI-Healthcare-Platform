from __future__ import annotations

from typing import Any, Optional

from app.tools.base_tool import BaseTool
from app.tools.config import ToolConfig
from app.tools.exceptions import ToolNotFoundError, ToolSelectorError
from app.tools.tool_context import ToolContext
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_factory import ToolFactory
from app.tools.tool_registry import get_global_registry
from app.tools.tool_result import ToolResult
from app.tools.tool_selector import ToolSelector


class ToolService:
    def __init__(self, registry=None, selector: Optional[ToolSelector] = None) -> None:
        self._registry = registry or get_global_registry()
        self._selector = selector or ToolSelector()

    def run(
        self,
        tool_type: str,
        action: str,
        user_id: str = "",
        user_role: str = "",
        patient_id: str = "",
        doctor_id: str = "",
        parameters: Optional[dict[str, Any]] = None,
        session_id: str = "",
        tool_config: Optional[ToolConfig] = None,
    ) -> ToolResult:
        try:
            tool = ToolFactory.create(tool_type, config=tool_config)
        except ToolNotFoundError as exc:
            return ToolResult.error_factory(
                error_message=str(exc),
                metadata={"error_type": "ToolNotFoundError", "tool_type": tool_type},
            )
        context = ToolContext(
            tool_name=tool_type,
            action=action,
            user_id=user_id,
            user_role=user_role,
            patient_id=patient_id,
            doctor_id=doctor_id,
            parameters=parameters or {},
            session_id=session_id,
        )
        executor = ToolExecutor(tool, config=tool_config or tool.config)
        return executor.execute(context)

    def run_with_tool(
        self, tool: BaseTool, context: ToolContext,
    ) -> ToolResult:
        executor = ToolExecutor(tool, config=tool.config)
        return executor.execute(context)

    def run_from_query(
        self,
        query: str,
        user_id: str = "",
        user_role: str = "",
        patient_id: str = "",
        doctor_id: str = "",
        parameters: Optional[dict[str, Any]] = None,
        session_id: str = "",
    ) -> ToolResult:
        try:
            tool_type, action = self._selector.select(query)
        except ToolSelectorError as exc:
            return ToolResult.error_factory(
                error_message=str(exc),
                metadata={"error_type": "ToolSelectorError", "query": query},
            )
        return self.run(
            tool_type=tool_type,
            action=action,
            user_id=user_id,
            user_role=user_role,
            patient_id=patient_id,
            doctor_id=doctor_id,
            parameters=parameters,
            session_id=session_id,
        )

    def list_tools(self) -> list[str]:
        return self._registry.list_tools()
