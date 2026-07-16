import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class PatientBase(BaseModel):
    email: EmailStr
    full_name: str = Field(max_length=255)
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class PatientCreate(PatientBase):
    password: str = Field(min_length=8, max_length=128)


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None


class PatientResponse(PatientBase):
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


class PatientSummary(BaseModel):
    id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    active_medicines_count: int = 0
    upcoming_appointments_count: int = 0
    pending_alerts_count: int = 0
    last_active: Optional[datetime] = None
