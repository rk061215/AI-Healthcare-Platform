from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentConfig:
    agent_type: str = "base"
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    timeout_seconds: float = 120.0
    enable_memory: bool = True
    enable_rag: bool = True
    enable_tools: bool = False
    enable_evaluation: bool = True
    enable_telemetry: bool = True
    log_level: str = "INFO"
    rag_top_k: int = 10
    rag_temperature: float = 0.3
    rag_max_tokens: int = 2048
    memory_type: str = "conversation"
    extra: dict = field(default_factory=dict)
