from __future__ import annotations

from typing import Optional

import pytest

from app.tools.base_tool import BaseTool
from app.tools.config import ToolConfig
from app.tools.exceptions import ToolValidationError
from app.tools.tool_context import ToolContext
from app.tools.tool_result import ToolResult


class SimpleTool(BaseTool):
    def execute(self, context: ToolContext) -> ToolResult:
        return ToolResult.ok(
            data={"message": "executed", "action": context.action},
            tool_name=context.tool_name,
            action=context.action,
        )


class FailingTool(BaseTool):
    def execute(self, context: ToolContext) -> ToolResult:
        return ToolResult.error_factory(
            error_message="execution failed",
            tool_name=context.tool_name,
            action=context.action,
        )


class ValidatingTool(BaseTool):
    def validate(self, context: ToolContext) -> None:
        if not context.parameters.get("required_field"):
            raise ToolValidationError("required_field is missing")

    def execute(self, context: ToolContext) -> ToolResult:
        return ToolResult.ok(data={"validated": True})


class AuthorizingTool(BaseTool):
    def authorize(self, context: ToolContext) -> bool:
        return context.user_role == "admin"

    def execute(self, context: ToolContext) -> ToolResult:
        return ToolResult.ok(data={"authorized": True})


class VerifyingTool(BaseTool):
    def execute(self, context: ToolContext) -> ToolResult:
        return ToolResult.ok(data={"value": "needs_verification"})

    def verify(self, result: ToolResult) -> ToolResult:
        result.metadata["verified"] = True
        return result


class AuditingTool(BaseTool):
    def __init__(self, config: Optional[ToolConfig] = None) -> None:
        super().__init__(config)
        self.audit_log: list[tuple[ToolContext, ToolResult]] = []

    def execute(self, context: ToolContext) -> ToolResult:
        return ToolResult.ok(data={"audited": True})

    def audit(self, context: ToolContext, result: ToolResult) -> None:
        self.audit_log.append((context, result))


@pytest.fixture
def sample_context() -> ToolContext:
    return ToolContext(
        tool_name="test_tool",
        action="test_action",
        user_id="user_1",
        user_role="patient",
        session_id="session_1",
    )


@pytest.fixture
def sample_config() -> ToolConfig:
    return ToolConfig(tool_type="test", max_retries=1)
