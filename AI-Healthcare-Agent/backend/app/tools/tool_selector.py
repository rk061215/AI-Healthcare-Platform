from __future__ import annotations

import re
from typing import Optional

from app.tools.exceptions import ToolSelectorError

TOOL_RULES: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"reschedule.*appointment", re.IGNORECASE), "appointment", "reschedule"),
    (re.compile(r"book.*appointment", re.IGNORECASE), "appointment", "book"),
    (re.compile(r"schedule.*appointment", re.IGNORECASE), "appointment", "book"),
    (re.compile(r"create.*appointment", re.IGNORECASE), "appointment", "book"),
    (re.compile(r"cancel.*appointment", re.IGNORECASE), "appointment", "cancel"),
    (re.compile(r"delete.*appointment", re.IGNORECASE), "appointment", "cancel"),
    (re.compile(r"remove.*appointment", re.IGNORECASE), "appointment", "cancel"),
    (re.compile(r"reschedule.*appointment", re.IGNORECASE), "appointment", "reschedule"),
    (re.compile(r"move.*appointment", re.IGNORECASE), "appointment", "reschedule"),
    (re.compile(r"change.*appointment", re.IGNORECASE), "appointment", "reschedule"),
    (re.compile(r"(upcoming|my|list|show|view)\s+appointment", re.IGNORECASE), "appointment", "list"),
    (re.compile(r"(appointment|appointments)", re.IGNORECASE), "appointment", "list"),
    (re.compile(r"doctor.*specializ", re.IGNORECASE), "doctor", "specialization"),
    (re.compile(r"doctor.*availab", re.IGNORECASE), "doctor", "availability"),
    (re.compile(r"(who is|show|get|my)\s+doctor", re.IGNORECASE), "doctor", "assigned_doctor"),
    (re.compile(r"summarize.*report", re.IGNORECASE), "report", "summarize"),
    (re.compile(r"summary.*report", re.IGNORECASE), "report", "summarize"),
    (re.compile(r"report.*(meta|detail|info|about)", re.IGNORECASE), "report", "metadata"),
    (re.compile(r"(my|get|show|view|list)\s+report", re.IGNORECASE), "report", "list"),
    (re.compile(r"active.*report", re.IGNORECASE), "patient", "active_reports"),
    (re.compile(r"current.*report", re.IGNORECASE), "patient", "active_reports"),
    (re.compile(r"my\s+profile", re.IGNORECASE), "patient", "get_profile"),
    (re.compile(r"patient.*info", re.IGNORECASE), "patient", "get_profile"),
    (re.compile(r"get.*patient", re.IGNORECASE), "patient", "get_profile"),
    (re.compile(r"explain.*(medicine|medication|drug|pill)", re.IGNORECASE), "medication", "explain"),
    (re.compile(r"(medicine|medication|pill|drug|prescription)", re.IGNORECASE), "medication", "schedule"),
]


class ToolSelector:
    def __init__(self, rules: Optional[list[tuple[re.Pattern, str, str]]] = None) -> None:
        self._rules = rules or TOOL_RULES

    def select(self, query: str) -> tuple[str, str]:
        for pattern, tool_name, action in self._rules:
            if pattern.search(query):
                return tool_name, action
        raise ToolSelectorError(f"No tool matched for query: '{query}'")

    def select_or_none(self, query: str) -> Optional[tuple[str, str]]:
        try:
            return self.select(query)
        except ToolSelectorError:
            return None
