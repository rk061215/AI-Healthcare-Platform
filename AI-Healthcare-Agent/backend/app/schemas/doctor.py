import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class DoctorBase(BaseModel):
    email: EmailStr
    full_name: str = Field(max_length=255)
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None


class DoctorCreate(DoctorBase):
    password: str = Field(min_length=8, max_length=128)


class DoctorUpdate(BaseModel):
    full_name: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None


class DoctorResponse(DoctorBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def convert_id_to_str(cls, v: object) -> str:
        if isinstance(v, uuid.UUID):
            return str(v)
        return str(v) if v else ""


class DoctorDashboard(BaseModel):
    total_patients: int
    pending_alerts: int
    upcoming_appointments: int
    recent_alerts: list
