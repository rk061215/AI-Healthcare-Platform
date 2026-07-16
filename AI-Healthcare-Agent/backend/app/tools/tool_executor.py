from __future__ import annotations

import time
import uuid
from typing import Optional

from app.tools.base_tool import BaseTool
from app.tools.config import ToolConfig
from app.tools.exceptions import (
    ToolAuthorizationError,
    ToolExecutionError,
    ToolRetryExhaustedError,
    ToolTimeoutError,
    ToolValidationError,
)
from app.tools.tool_context import ToolContext
from app.tools.tool_result import ToolResult


class ToolExecutor:
    def __init__(self, tool: BaseTool, config: Optional[ToolConfig] = None) -> None:
        self._tool = tool
        self._config = config or tool.config

    @property
    def tool(self) -> BaseTool:
        return self._tool

    def execute(self, context: ToolContext) -> ToolResult:
        context.trace_id = context.trace_id or uuid.uuid4().hex[:16]
        start_time = time.time()

        try:
            if self._config.require_validation:
                self._tool.validate(context)

            if self._config.require_authorization:
                if not self._tool.authorize(context):
                    raise ToolAuthorizationError(
                        f"User '{context.user_id}' is not authorized for "
                        f"tool '{context.tool_name}' action '{context.action}'"
                    )

            result = self._execute_with_retry(context)

            if self._config.require_verification:
                result = self._tool.verify(result)

            if self._config.require_audit:
                self._tool.audit(context, result)

            duration = (time.time() - start_time) * 1000
            result.duration_ms = duration
            result.tool_name = context.tool_name
            result.action = context.action

            return result

        except (ToolTimeoutError, ToolRetryExhaustedError, ToolAuthorizationError,
                ToolValidationError) as exc:
            duration = (time.time() - start_time) * 1000
            return ToolResult.error_factory(
                error_message=str(exc),
                tool_name=context.tool_name,
                action=context.action,
                duration_ms=duration,
                metadata={"error_type": type(exc).__name__, "trace_id": context.trace_id},
            )

        except Exception as exc:
            duration = (time.time() - start_time) * 1000
            return ToolResult.error_factory(
                error_message=str(exc),
                tool_name=context.tool_name,
                action=context.action,
                duration_ms=duration,
                metadata={"error_type": type(exc).__name__, "trace_id": context.trace_id},
            )

        finally:
            self._tool.cleanup(context)

    def _execute_with_retry(self, context: ToolContext) -> ToolResult:
        last_exc: Optional[Exception] = None
        for attempt in range(self._config.max_retries):
            try:
                return self._tool.execute(context)
            except Exception as exc:
                last_exc = exc
                if attempt < self._config.max_retries - 1:
                    time.sleep(self._config.retry_delay_seconds)
        raise ToolRetryExhaustedError(
            f"All {self._config.max_retries} retries failed: {last_exc}"
        ) from last_exc
