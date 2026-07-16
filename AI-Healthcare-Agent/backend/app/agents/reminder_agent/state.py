from typing import Any, Optional

from typing_extensions import TypedDict


class ReminderAgentState(TypedDict):
    patient_id: str
    medicines: list[dict[str, Any]]
    schedule: Optional[list[dict[str, Any]]]
    reminders: Optional[list[dict[str, Any]]]
    adherence_status: Optional[dict[str, Any]]
    error: Optional[str]
