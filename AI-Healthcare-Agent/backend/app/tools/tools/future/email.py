from app.tools.base_tool import BaseTool
from app.tools.tool_context import ToolContext
from app.tools.tool_result import ToolResult


class EmailTool(BaseTool):
    def can_handle(self) -> bool:
        return False

    def execute(self, context: ToolContext) -> ToolResult:
        return ToolResult.error_factory(
                error_message="EmailTool is not yet implemented",
            tool_name=context.tool_name,
            action=context.action,
        )
