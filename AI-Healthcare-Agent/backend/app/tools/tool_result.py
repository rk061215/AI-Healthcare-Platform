from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error_message: Optional[str] = None
    tool_name: str = ""
    action: str = ""
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def error(self) -> Optional[str]:
        return self.error_message

    @classmethod
    def ok(
        cls,
        data: Any = None,
        tool_name: str = "",
        action: str = "",
        duration_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        return cls(
            success=True,
            data=data,
            tool_name=tool_name,
            action=action,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

    @classmethod
    def error_factory(
        cls,
        error_message: str,
        tool_name: str = "",
        action: str = "",
        duration_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> ToolResult:
        return cls(
            success=False,
            error_message=error_message,
            tool_name=tool_name,
            action=action,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )
