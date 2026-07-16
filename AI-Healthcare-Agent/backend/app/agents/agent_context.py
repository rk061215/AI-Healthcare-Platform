from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AgentContext:
    query: str
    session_id: str
    patient_id: str = ""
    document_id: Optional[str] = None
    report_id: Optional[str] = None
    document_type: Optional[str] = None
    document_sections: list[str] = field(default_factory=list)
    memory_entries: list[dict[str, Any]] = field(default_factory=list)
    retrieved_evidence: list[dict[str, Any]] = field(default_factory=list)
    active_document: Optional[str] = None
    language: str = "en"
    metadata: dict[str, Any] = field(default_factory=dict)
    config_overrides: dict[str, Any] = field(default_factory=dict)
