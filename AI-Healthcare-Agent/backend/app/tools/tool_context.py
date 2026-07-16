from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolContext:
    tool_name: str
    action: str = ""
    user_id: str = ""
    user_role: str = ""
    patient_id: str = ""
    doctor_id: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    session_id: str = ""
    trace_id: str = ""
