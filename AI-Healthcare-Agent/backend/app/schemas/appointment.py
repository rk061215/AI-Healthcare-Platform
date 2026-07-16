from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, field_validator

from app.database.enums import RecurrenceFrequency


class AppointmentBase(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    scheduled_at: datetime
    status: str = "scheduled"


class AppointmentCreate(BaseModel):
    doctor_id: str
    scheduled_at: datetime
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    duration_minutes: int = Field(default=30, ge=15, le=240)
    timezone: str = "UTC"


class AppointmentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = None
    follow_up_notes: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=15, le=240)


class AppointmentReschedule(BaseModel):
    scheduled_at: datetime
    reason: Optional[str] = Field(None, max_length=500)
    timezone: str = "UTC"


class AppointmentCancel(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class AppointmentResponse(AppointmentBase):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    duration_minutes: int = 30
    follow_up_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    rescheduled_from: Optional[UUID] = None
    timezone: str = "UTC"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "patient_id", "doctor_id", "rescheduled_from")
    @classmethod
    def serialize_uuid(cls, v: Optional[UUID]) -> Optional[str]:
        return str(v) if v else None


class AppointmentDetailResponse(AppointmentResponse):
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_specialization: Optional[str] = None
    audit_logs: list[dict] = []


class RecurringAppointmentCreate(BaseModel):
    doctor_id: str
    scheduled_at: datetime
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    duration_minutes: int = Field(default=30, ge=15, le=240)
    timezone: str = "UTC"
    frequency: RecurrenceFrequency
    interval_count: int = Field(default=1, ge=1, le=90)
    weekdays: Optional[list[int]] = None
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = Field(None, ge=1, le=365)

    @field_validator("weekdays")
    @classmethod
    def validate_weekdays(cls, v: Optional[list[int]]) -> Optional[list[int]]:
        if v is not None:
            for d in v:
                if d < 0 or d > 6:
                    raise ValueError("Weekdays must be 0 (Mon) to 6 (Sun)")
        return v


class RecurringAppointmentResponse(BaseModel):
    id: UUID
    appointment_id: UUID
    frequency: str
    interval_count: int
    weekdays: Optional[str] = None
    end_date: Optional[datetime] = None
    max_occurrences: Optional[int] = None
    occurrences_generated: int
    is_active: bool

    model_config = {"from_attributes": True}

    @field_serializer("id", "appointment_id")
    @classmethod
    def serialize_uuid(cls, v: UUID) -> str:
        return str(v)


class DoctorAvailabilitySlot(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    is_available: bool = True
    slot_duration_minutes: int = Field(default=30, ge=15, le=120)


class DoctorAvailabilityResponse(BaseModel):
    id: UUID
    doctor_id: UUID
    day_of_week: int
    start_time: str
    end_time: str
    is_available: bool
    slot_duration_minutes: int

    model_config = {"from_attributes": True}

    @field_serializer("id", "doctor_id")
    @classmethod
    def serialize_uuid(cls, v: UUID) -> str:
        return str(v)


class AvailableSlot(BaseModel):
    start: datetime
    end: datetime
    doctor_id: str


class AppointmentAuditLogResponse(BaseModel):
    id: UUID
    appointment_id: UUID
    action: str
    user_id: Optional[UUID] = None
    user_role: Optional[str] = None
    changes: Optional[dict] = None
    timestamp: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "appointment_id", "user_id")
    @classmethod
    def serialize_uuid(cls, v: Optional[UUID]) -> Optional[str]:
        return str(v) if v else None
