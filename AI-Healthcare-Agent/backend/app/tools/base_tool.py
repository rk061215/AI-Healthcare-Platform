from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.tools.config import ToolConfig
from app.tools.tool_context import ToolContext
from app.tools.tool_result import ToolResult


class BaseTool(ABC):
    def __init__(self, config: Optional[ToolConfig] = None) -> None:
        self._config = config or ToolConfig()

    @property
    def config(self) -> ToolConfig:
        return self._config

    def validate(self, context: ToolContext) -> None:
        """Validate input parameters before execution.
        Override to add domain-specific validation.
        Raises ToolValidationError on failure.
        """
        if not context.tool_name:
            from app.tools.exceptions import ToolValidationError
            raise ToolValidationError("tool_name is required")

    def authorize(self, context: ToolContext) -> bool:
        """Check if the user is authorized to perform this action.
        Override to add domain-specific authorization.
        Returns True if authorized, False otherwise.
        """
        return True

    @abstractmethod
    def execute(self, context: ToolContext) -> ToolResult:
        """Execute the tool's domain logic.
        Must be implemented by subclasses.
        """

    def verify(self, result: ToolResult) -> ToolResult:
        """Verify the output quality of the execution result.
        Override to add domain-specific verification.
        Returns the (possibly modified) result, or raises ToolVerificationError.
        """
        return result

    def audit(self, context: ToolContext, result: ToolResult) -> None:
        """Log execution metadata for auditing.
        Override to add domain-specific audit logging.
        """

    def cleanup(self, context: ToolContext) -> None:
        """Release any resources held by the tool.
        Override if the tool holds connections or temporary resources.
        """
