from __future__ import annotations

import pytest

from app.tools.config import ToolConfig
from app.tools.exceptions import (
    ToolAuthorizationError,
    ToolExecutionError,
    ToolRetryExhaustedError,
    ToolValidationError,
)
from app.tools.tool_context import ToolContext
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_result import ToolResult
from tests.test_tools.conftest import (
    AuditingTool,
    AuthorizingTool,
    SimpleTool,
    ValidatingTool,
    VerifyingTool,
)


class TestToolExecutor:
    def test_full_lifecycle(self):
        tool = SimpleTool()
        executor = ToolExecutor(tool)
        ctx = ToolContext(tool_name="test", action="act", user_id="u1", user_role="patient")
        result = executor.execute(ctx)
        assert result.success is True
        assert result.tool_name == "test"
        assert result.action == "act"
        assert result.duration_ms >= 0

    def test_executor_property(self):
        tool = SimpleTool()
        executor = ToolExecutor(tool)
        assert executor.tool is tool

    def test_validation_failure(self):
        tool = ValidatingTool()
        executor = ToolExecutor(tool)
        ctx = ToolContext(tool_name="test", action="act")
        result = executor.execute(ctx)
        assert result.success is False
        assert "required_field" in (result.error or "")

    def test_authorization_failure(self):
        tool = AuthorizingTool()
        executor = ToolExecutor(tool)
        ctx = ToolContext(tool_name="test", action="act", user_id="u1", user_role="patient")
        result = executor.execute(ctx)
        assert result.success is False
        assert "not authorized" in (result.error or "").lower()

    def test_authorization_bypass(self):
        tool = AuthorizingTool()
        config = ToolConfig(require_authorization=False)
        executor = ToolExecutor(tool, config=config)
        ctx = ToolContext(tool_name="test", action="act", user_id="u1", user_role="patient")
        result = executor.execute(ctx)
        assert result.success is True

    def test_validation_bypass(self):
        tool = ValidatingTool()
        config = ToolConfig(require_validation=False)
        executor = ToolExecutor(tool, config=config)
        ctx = ToolContext(tool_name="test", action="act")
        result = executor.execute(ctx)
        assert result.success is True

    def test_verification_bypass(self):
        tool = VerifyingTool()
        config = ToolConfig(require_verification=False)
        executor = ToolExecutor(tool, config=config)
        ctx = ToolContext(tool_name="test", action="act")
        result = executor.execute(ctx)
        assert result.success is True
        assert "verified" not in result.metadata

    def test_audit_invoked(self):
        tool = AuditingTool()
        executor = ToolExecutor(tool)
        ctx = ToolContext(tool_name="test", action="act")
        executor.execute(ctx)
        assert len(tool.audit_log) == 1

    def test_audit_bypass(self):
        tool = AuditingTool()
        config = ToolConfig(require_audit=False)
        executor = ToolExecutor(tool, config=config)
        ctx = ToolContext(tool_name="test", action="act")
        executor.execute(ctx)
        assert len(tool.audit_log) == 0

    def test_cleanup_called(self):
        cleanup_called = [False]

        class CleanupTool(SimpleTool):
            def cleanup(self, context: ToolContext) -> None:
                cleanup_called[0] = True

        tool = CleanupTool()
        executor = ToolExecutor(tool)
        ctx = ToolContext(tool_name="test", action="act")
        executor.execute(ctx)
        assert cleanup_called[0] is True

    def test_cleanup_called_on_error(self):
        cleanup_called = [False]

        class ErrorTool(SimpleTool):
            def execute(self, context: ToolContext) -> ToolResult:
                raise ValueError("test error")

            def cleanup(self, context: ToolContext) -> None:
                cleanup_called[0] = True

        tool = ErrorTool()
        executor = ToolExecutor(tool)
        ctx = ToolContext(tool_name="test", action="act")
        executor.execute(ctx)
        assert cleanup_called[0] is True

    def test_retry_on_failure(self):
        attempt_count = [0]

        class RetryTool(SimpleTool):
            def execute(self, context: ToolContext) -> ToolResult:
                attempt_count[0] += 1
                if attempt_count[0] < 2:
                    raise ValueError("transient error")
                return ToolResult.ok(data={"success": True})

        config = ToolConfig(max_retries=3, retry_delay_seconds=0.01)
        tool = RetryTool()
        executor = ToolExecutor(tool, config=config)
        ctx = ToolContext(tool_name="test", action="act")
        result = executor.execute(ctx)
        assert result.success is True
        assert attempt_count[0] == 2
