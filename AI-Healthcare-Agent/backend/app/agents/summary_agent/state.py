from typing import Any, Optional

from typing_extensions import TypedDict


class SummaryAgentState(TypedDict):
    patient_id: str
    patient_data: Optional[dict[str, Any]]
    summary: Optional[str]
    error: Optional[str]
