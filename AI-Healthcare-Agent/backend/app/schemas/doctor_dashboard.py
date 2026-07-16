import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DoctorProfile(BaseModel):
    id: str
    full_name: str
    email: str
    specialization: Optional[str] = None
    phone: Optional[str] = None
    hospital_name: Optional[str] = None
    years_of_experience: Optional[int] = None

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def convert_id_to_str(cls, v: object) -> str:
        if isinstance(v, uuid.UUID):
            return str(v)
        return str(v) if v else ""


class DoctorAnalytics(BaseModel):
    total_patients: int = 0
    active_patients: int = 0
    total_appointments: int = 0
    upcoming_appointments: int = 0
    pending_reports: int = 0
    unread_alerts: int = 0
    pending_follow_ups: int = 0


class DashboardPatientSummary(BaseModel):
    id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    date_of_birth: Optional[date] = None
    active_medicines_count: int = 0
    upcoming_appointments_count: int = 0
    pending_alerts_count: int = 0
    last_active: Optional[datetime] = None
    overall_adherence_rate: Optional[float] = None
    assigned_at: Optional[datetime] = None


class DoctorAppointmentSummary(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: datetime
    status: str
    patient_phone: Optional[str] = None
    patient_dob: Optional[date] = None
    created_at: datetime


class DoctorReportSummary(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    title: Optional[str] = None
    file_type: Optional[str] = None
    status: str
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    medicine_count: int = 0
    doctor_id: Optional[str] = None


class DoctorAlertItem(BaseModel):
    id: str
    patient_id: str
    patient_name: str
    risk_level: str
    symptoms: str
    analysis: Optional[str] = None
    is_acknowledged: bool
    created_at: datetime
    patient_phone: Optional[str] = None


class DoctorDashboardOverview(BaseModel):
    doctor: DoctorProfile
    analytics: DoctorAnalytics
    recent_alerts: list[DoctorAlertItem] = []


class DoctorAISummaryItem(BaseModel):
    patient_id: str
    patient_name: str
    overall_adherence_rate: float = 0.0
    alert_count: int = 0
    highest_risk_alert: Optional[str] = None
    generated_at: Optional[str] = None
    medicines_count: int = 0
    recent_symptoms: list[str] = []
