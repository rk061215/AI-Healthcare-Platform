from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SymptomCheckRequest(BaseModel):
    symptoms: str = Field(min_length=10, max_length=2000)


class SymptomCheckResponse(BaseModel):
    risk_level: str
    analysis: str
    recommendations: list[str]
    disclaimer: str


class EmergencyAlertResponse(BaseModel):
    id: str
    patient_id: str
    risk_level: str
    symptoms: str
    analysis: Optional[str] = None
    is_acknowledged: bool
    acknowledged_by: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
