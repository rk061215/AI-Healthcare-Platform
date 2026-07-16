from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolConfig:
    tool_type: str = "base"
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    timeout_seconds: float = 60.0
    require_authorization: bool = True
    require_validation: bool = True
    require_verification: bool = True
    require_audit: bool = True
    log_level: str = "INFO"
    extra: dict[str, Any] = field(default_factory=dict)
