from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class MedicineBase(BaseModel):
    name: str = Field(max_length=255)
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    route: Optional[str] = None
    instructions: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class MedicineCreate(MedicineBase):
    report_id: str
    patient_id: str


class MedicineUpdate(BaseModel):
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    route: Optional[str] = None
    instructions: Optional[str] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None


class MedicineResponse(MedicineBase):
    id: str
    report_id: str
    patient_id: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MedicineWithAdherence(MedicineResponse):
    adherence_rate: float = 0.0
    total_doses: int = 0
    taken_doses: int = 0
    missed_doses: int = 0
