from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AdherenceLogCreate(BaseModel):
    medicine_id: str
    scheduled_time: datetime
    status: str = "pending"
    notes: Optional[str] = None


class AdherenceLogResponse(BaseModel):
    id: str
    medicine_id: str
    patient_id: str
    scheduled_time: datetime
    taken_at: Optional[datetime] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdherenceStats(BaseModel):
    total_doses: int
    taken_doses: int
    missed_doses: int
    skipped_doses: int
    pending_doses: int
    adherence_rate: float
    period_start: datetime
    period_end: datetime


class TodaySchedule(BaseModel):
    medicine_id: str
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    scheduled_time: datetime
    status: str
    is_taken: bool
