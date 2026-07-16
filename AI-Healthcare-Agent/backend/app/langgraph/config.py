from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LangGraphConfig:
    graph_name: str = "medical_qa"
    enable_checkpointing: bool = True
    enable_events: bool = True
    enable_metrics: bool = True
    execution_timeout_ms: float = 60000.0
    node_timeout_ms: float = 30000.0
    max_retries: int = 2
    retry_delay_seconds: float = 0.5
    checkpoint_provider: str = "in_memory"
    checkpoint_config: dict[str, Any] = field(default_factory=dict)
    metrics_provider: str = "in_memory"
    metrics_config: dict[str, Any] = field(default_factory=dict)
