import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundException
from app.models.adherence_log import AdherenceLog
from app.models.appointment import Appointment
from app.models.chat_history import ChatHistory
from app.models.doctor import Doctor
from app.models.emergency_alert import EmergencyAlert
from app.models.medicine import Medicine
from app.models.patient import Patient
from app.models.patient_doctor import PatientDoctor
from app.models.report import Report
from app.schemas.dashboard import (
    AIStatusCard,
    AdherenceDay,
    AppointmentSummary,
    DashboardOverview,
    MedicineWithSchedule,
    ReminderHistoryItem,
    ReportSummary,
    TimelineEvent,
    TodayScheduleItem,
)
from app.schemas.pagination import PaginatedResponse


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_overview(self, patient_id: str) -> DashboardOverview:
        pid = uuid.UUID(patient_id)
        patient = self.db.get(Patient, pid)
        if not patient:
            raise NotFoundException("Patient", patient_id)

        active_meds = self.db.execute(
            select(func.count()).where(
                Medicine.patient_id == pid, Medicine.is_active == True
            )
        ).scalar() or 0

        total_reports = self.db.execute(
            select(func.count()).where(Report.patient_id == pid)
        ).scalar() or 0

        upcoming_appts = self.db.execute(
            select(func.count()).where(
                Appointment.patient_id == pid,
                Appointment.scheduled_at >= datetime.now(timezone.utc),
                Appointment.status.in_(["scheduled", "confirmed"]),
            )
        ).scalar() or 0

        today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
        today_end = today_start + timedelta(days=1)

        total_doses = self.db.execute(
            select(func.count()).where(
                AdherenceLog.patient_id == pid,
                AdherenceLog.scheduled_time >= today_start,
                AdherenceLog.scheduled_time < today_end,
            )
        ).scalar() or 0

        taken_doses = self.db.execute(
            select(func.count()).where(
                AdherenceLog.patient_id == pid,
                AdherenceLog.scheduled_time >= today_start,
                AdherenceLog.scheduled_time < today_end,
                AdherenceLog.status == "taken",
            )
        ).scalar() or 0

        missed_doses = self.db.execute(
            select(func.count()).where(
                AdherenceLog.patient_id == pid,
                AdherenceLog.scheduled_time >= today_start,
                AdherenceLog.scheduled_time < today_end,
                AdherenceLog.status == "missed",
            )
        ).scalar() or 0

        adherence_rate = round((taken_doses / total_doses * 100) if total_doses > 0 else 0.0, 1)

        pending_alerts = self.db.execute(
            select(func.count()).where(
                EmergencyAlert.patient_id == pid,
                EmergencyAlert.is_acknowledged == False,
            )
        ).scalar() or 0

        last_chat = self.db.execute(
            select(ChatHistory.created_at)
            .where(ChatHistory.patient_id == pid, ChatHistory.role == "user")
            .order_by(ChatHistory.created_at.desc())
            .limit(1)
        ).scalar()

        doctor_assignments = self.db.execute(
            select(Doctor)
            .join(PatientDoctor, PatientDoctor.doctor_id == Doctor.id)
            .where(PatientDoctor.patient_id == pid, PatientDoctor.is_active == True)
        ).scalars().all()

        return DashboardOverview(
            patient_name=patient.full_name,
            patient_email=patient.email,
            patient_phone=patient.phone,
            patient_dob=patient.date_of_birth,
            patient_gender=patient.gender.value if patient.gender else None,
            patient_blood_group=patient.blood_group.value if patient.blood_group else None,
            emergency_contact=patient.emergency_contact,
            emergency_phone=patient.emergency_phone,
            active_medicines_count=active_meds,
            total_reports_count=total_reports,
            upcoming_appointments_count=upcoming_appts,
            adherence_rate=adherence_rate,
            total_doses=total_doses,
            taken_doses=taken_doses,
            missed_doses=missed_doses,
            pending_alerts_count=pending_alerts,
            last_chat_at=last_chat,
            assigned_doctors=[
                {"id": str(d.id), "full_name": d.full_name, "specialization": d.specialization}
                for d in doctor_assignments
            ],
        )

    def get_medicines(
        self, patient_id: str, page: int = 1, per_page: int = 20
    ) -> PaginatedResponse[MedicineWithSchedule]:
        pid = uuid.UUID(patient_id)

        total = self.db.execute(
            select(func.count()).where(Medicine.patient_id == pid)
        ).scalar() or 0

        query = (
            select(Medicine)
            .where(Medicine.patient_id == pid)
            .order_by(Medicine.is_active.desc(), Medicine.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        medicines = self.db.execute(query).scalars().all()

        items = []
        for med in medicines:
            today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
            today_end = today_start + timedelta(days=1)

            total_doses = self.db.execute(
                select(func.count()).where(
                    AdherenceLog.medicine_id == med.id,
                    AdherenceLog.scheduled_time >= today_start,
                    AdherenceLog.scheduled_time < today_end,
                )
            ).scalar() or 0
            taken_doses = self.db.execute(
                select(func.count()).where(
                    AdherenceLog.medicine_id == med.id,
                    AdherenceLog.scheduled_time >= today_start,
                    AdherenceLog.scheduled_time < today_end,
                    AdherenceLog.status == "taken",
                )
            ).scalar() or 0
            missed_doses = self.db.execute(
                select(func.count()).where(
                    AdherenceLog.medicine_id == med.id,
                    AdherenceLog.scheduled_time >= today_start,
                    AdherenceLog.scheduled_time < today_end,
                    AdherenceLog.status == "missed",
                )
            ).scalar() or 0
            rate = round((taken_doses / total_doses * 100) if total_doses > 0 else 0.0, 1)

            items.append(
                MedicineWithSchedule(
                    id=str(med.id),
                    name=med.name,
                    dosage=med.dosage,
                    frequency=med.frequency,
                    route=med.route.value if med.route else None,
                    instructions=med.instructions,
                    start_date=med.start_date,
                    end_date=med.end_date,
                    is_active=med.is_active,
                    adherence_rate=rate,
                    total_doses=total_doses,
                    taken_doses=taken_doses,
                    missed_doses=missed_doses,
                    created_at=med.created_at,
                )
            )

        return PaginatedResponse.create(items, total, page, per_page)

    def get_appointments(
        self, patient_id: str, page: int = 1, per_page: int = 10, status_filter: str | None = None
    ) -> PaginatedResponse[AppointmentSummary]:
        pid = uuid.UUID(patient_id)

        base_query = select(Appointment).where(Appointment.patient_id == pid)
        count_query = select(func.count()).where(Appointment.patient_id == pid)

        if status_filter:
            base_query = base_query.where(Appointment.status == status_filter)
            count_query = count_query.where(Appointment.status == status_filter)

        total = self.db.execute(count_query).scalar() or 0

        query = (
            base_query
            .options(joinedload(Appointment.doctor))
            .order_by(Appointment.scheduled_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        appointments = self.db.execute(query).unique().scalars().all()

        items = [
            AppointmentSummary(
                id=str(a.id),
                doctor_name=a.doctor.full_name if a.doctor else "Unknown",
                doctor_specialization=a.doctor.specialization if a.doctor else None,
                title=a.title,
                description=a.description,
                scheduled_at=a.scheduled_at,
                status=a.status.value if a.status else "unknown",
            )
            for a in appointments
        ]

        return PaginatedResponse.create(items, total, page, per_page)

    def get_reports(
        self, patient_id: str, page: int = 1, per_page: int = 10, status_filter: str | None = None
    ) -> PaginatedResponse[ReportSummary]:
        pid = uuid.UUID(patient_id)

        base_query = select(Report).where(Report.patient_id == pid)
        count_query = select(func.count()).where(Report.patient_id == pid)

        if status_filter:
            base_query = base_query.where(Report.status == status_filter)
            count_query = count_query.where(Report.status == status_filter)

        total = self.db.execute(count_query).scalar() or 0

        query = (
            base_query
            .order_by(Report.uploaded_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        reports = self.db.execute(query).scalars().all()

        items = []
        for r in reports:
            med_count = self.db.execute(
                select(func.count()).where(Medicine.report_id == r.id)
            ).scalar() or 0
            items.append(
                ReportSummary(
                    id=str(r.id),
                    title=r.title,
                    file_type=r.file_type,
                    status=r.status.value if r.status else "unknown",
                    uploaded_at=r.uploaded_at,
                    processed_at=r.processed_at,
                    medicine_count=med_count,
                )
            )

        return PaginatedResponse.create(items, total, page, per_page)

    def get_today_schedule(self, patient_id: str) -> list[TodayScheduleItem]:
        pid = uuid.UUID(patient_id)
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
        today_end = today_start + timedelta(days=1)

        logs = self.db.execute(
            select(AdherenceLog)
            .options(joinedload(AdherenceLog.medicine))
            .where(
                AdherenceLog.patient_id == pid,
                AdherenceLog.scheduled_time >= today_start,
                AdherenceLog.scheduled_time < today_end,
            )
            .order_by(AdherenceLog.scheduled_time.asc())
        ).unique().scalars().all()

        return [
            TodayScheduleItem(
                medicine_id=str(log.medicine_id),
                medicine_name=log.medicine.name if log.medicine else "Unknown",
                dosage=log.medicine.dosage if log.medicine else None,
                frequency=log.medicine.frequency if log.medicine else None,
                scheduled_time=log.scheduled_time.strftime("%H:%M"),
                status=log.status.value if log.status else "pending",
                is_taken=log.status == "taken",
            )
            for log in logs
        ]

    def get_timeline(self, patient_id: str, days: int = 30) -> list[TimelineEvent]:
        pid = uuid.UUID(patient_id)
        since = datetime.now(timezone.utc) - timedelta(days=days)
        events: list[TimelineEvent] = []

        reports = self.db.execute(
            select(Report)
            .where(Report.patient_id == pid, Report.uploaded_at >= since)
            .order_by(Report.uploaded_at.desc())
        ).scalars().all()
        for r in reports:
            events.append(
                TimelineEvent(
                    event_type="report",
                    title=f"Report uploaded: {r.title or 'Untitled'}",
                    description=f"Status: {r.status.value if r.status else 'unknown'}",
                    timestamp=r.uploaded_at,
                    icon="file-text",
                )
            )

        appointments = self.db.execute(
            select(Appointment)
            .options(joinedload(Appointment.doctor))
            .where(Appointment.patient_id == pid, Appointment.scheduled_at >= since)
            .order_by(Appointment.scheduled_at.desc())
        ).unique().scalars().all()
        for a in appointments:
            events.append(
                TimelineEvent(
                    event_type="appointment",
                    title=f"Appointment with Dr. {a.doctor.full_name if a.doctor else 'Unknown'}",
                    description=f"Status: {a.status.value if a.status else 'unknown'}",
                    timestamp=a.scheduled_at,
                    icon="calendar",
                )
            )

        alerts = self.db.execute(
            select(EmergencyAlert)
            .where(EmergencyAlert.patient_id == pid, EmergencyAlert.created_at >= since)
            .order_by(EmergencyAlert.created_at.desc())
        ).scalars().all()
        for a in alerts:
            events.append(
                TimelineEvent(
                    event_type="emergency",
                    title=f"Emergency alert — {a.risk_level.value.upper() if a.risk_level else 'UNKNOWN'} risk",
                    description=a.symptoms[:100] if a.symptoms else None,
                    timestamp=a.created_at,
                    icon="alert-triangle",
                )
            )

        medicines = self.db.execute(
            select(Medicine)
            .where(Medicine.patient_id == pid, Medicine.created_at >= since)
            .order_by(Medicine.created_at.desc())
        ).scalars().all()
        for m in medicines:
            events.append(
                TimelineEvent(
                    event_type="medicine",
                    title=f"Medicine added: {m.name}",
                    description=f"{m.dosage or ''} {m.frequency or ''}".strip() or None,
                    timestamp=m.created_at,
                    icon="pill",
                )
            )

        events.sort(key=lambda e: e.timestamp, reverse=True)
        return events

    def get_reminder_history(
        self, patient_id: str, page: int = 1, per_page: int = 20
    ) -> PaginatedResponse[ReminderHistoryItem]:
        pid = uuid.UUID(patient_id)

        total = self.db.execute(
            select(func.count()).where(AdherenceLog.patient_id == pid)
        ).scalar() or 0

        query = (
            select(AdherenceLog)
            .options(joinedload(AdherenceLog.medicine))
            .where(AdherenceLog.patient_id == pid)
            .order_by(AdherenceLog.scheduled_time.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        logs = self.db.execute(query).unique().scalars().all()

        items = [
            ReminderHistoryItem(
                id=str(log.id),
                medicine_name=log.medicine.name if log.medicine else "Unknown",
                scheduled_time=log.scheduled_time,
                taken_at=log.taken_at,
                status=log.status.value if log.status else "unknown",
            )
            for log in logs
        ]

        return PaginatedResponse.create(items, total, page, per_page)

    def get_ai_status(self, patient_id: str) -> AIStatusCard:
        pid = uuid.UUID(patient_id)

        total_chats = self.db.execute(
            select(func.count()).where(
                ChatHistory.patient_id == pid, ChatHistory.role == "user"
            )
        ).scalar() or 0

        last_interaction = self.db.execute(
            select(ChatHistory.created_at)
            .where(ChatHistory.patient_id == pid)
            .order_by(ChatHistory.created_at.desc())
            .limit(1)
        ).scalar()

        return AIStatusCard(
            status="ready" if total_chats > 0 else "new",
            last_interaction=last_interaction,
            total_chats=total_chats,
            pending_follow_ups=0,
            message="Your AI assistant is ready to help with any health questions."
            if total_chats > 0
            else "Start a conversation with your AI health assistant.",
        )
