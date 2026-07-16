from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class DashboardOverview(BaseModel):
    patient_name: str
    patient_email: str
    patient_phone: Optional[str] = None
    patient_dob: Optional[date] = None
    patient_gender: Optional[str] = None
    patient_blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    active_medicines_count: int = 0
    total_reports_count: int = 0
    upcoming_appointments_count: int = 0
    adherence_rate: float = 0.0
    total_doses: int = 0
    taken_doses: int = 0
    missed_doses: int = 0
    pending_alerts_count: int = 0
    last_chat_at: Optional[datetime] = None
    assigned_doctors: list[dict] = []


class MedicineWithSchedule(BaseModel):
    id: str
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    instructions: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool
    adherence_rate: float = 0.0
    total_doses: int = 0
    taken_doses: int = 0
    missed_doses: int = 0
    created_at: datetime


class AppointmentSummary(BaseModel):
    id: str
    doctor_name: str
    doctor_specialization: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: datetime
    status: str


class ReportSummary(BaseModel):
    id: str
    title: Optional[str] = None
    file_type: Optional[str] = None
    status: str
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    medicine_count: int = 0


class TodayScheduleItem(BaseModel):
    medicine_id: str
    medicine_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    scheduled_time: str
    status: str
    is_taken: bool


class AdherenceDay(BaseModel):
    date: date
    total: int = 0
    taken: int = 0
    missed: int = 0
    rate: float = 0.0


class ReminderHistoryItem(BaseModel):
    id: str
    medicine_name: str
    scheduled_time: datetime
    taken_at: Optional[datetime] = None
    status: str


class TimelineEvent(BaseModel):
    event_type: str
    title: str
    description: Optional[str] = None
    timestamp: datetime
    icon: Optional[str] = None


class AIStatusCard(BaseModel):
    status: str = "ready"
    last_interaction: Optional[datetime] = None
    total_chats: int = 0
    pending_follow_ups: int = 0
    message: str = "Your AI assistant is ready to help with any health questions."
