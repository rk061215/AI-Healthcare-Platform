from typing import Optional

from typing_extensions import TypedDict


class EmergencyAgentState(TypedDict):
    symptoms: str
    patient_id: str
    risk_level: Optional[str]
    analysis: Optional[str]
    recommendations: Optional[list[str]]
    disclaimer: Optional[str]
    error: Optional[str]
