import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select, case
from sqlalchemy.orm import Session, joinedload

from app.database.enums import (
    AdherenceStatus,
    AppointmentStatus,
    ReportStatus,
    RiskLevel,
)
from app.models.adherence_log import AdherenceLog
from app.models.appointment import Appointment
from app.models.chat_history import ChatHistory
from app.models.doctor import Doctor
from app.models.emergency_alert import EmergencyAlert
from app.models.medicine import Medicine
from app.models.patient import Patient
from app.models.patient_doctor import PatientDoctor
from app.models.report import Report
from app.schemas.pagination import PaginatedResponse


class DoctorDashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_overview(self, doctor_id: str) -> dict:
        doctor_uuid = uuid.UUID(doctor_id)

        doctor = self.db.get(Doctor, doctor_uuid)
        if not doctor:
            raise ValueError("Doctor not found")

        assigned_patient_ids = self._get_assigned_patient_ids(doctor_uuid)

        now = datetime.now(timezone.utc)

        total_patients = len(assigned_patient_ids)

        active_patients = 0
        if assigned_patient_ids:
            active_patients = self.db.execute(
                select(func.count(Patient.id)).where(
                    Patient.id.in_(assigned_patient_ids),
                    Patient.deleted_at.is_(None),
                )
            ).scalar() or 0

        total_appts = self.db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.doctor_id == doctor_uuid,
                Appointment.deleted_at.is_(None),
            )
        ).scalar() or 0

        upcoming_appts = self.db.execute(
            select(func.count(Appointment.id)).where(
                Appointment.doctor_id == doctor_uuid,
                Appointment.scheduled_at >= now,
                Appointment.status.in_(
                    [AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]
                ),
                Appointment.deleted_at.is_(None),
            )
        ).scalar() or 0

        pending_reports = self.db.execute(
            select(func.count(Report.id)).where(
                Report.patient_id.in_(assigned_patient_ids) if assigned_patient_ids else False,
                Report.status.in_([ReportStatus.PENDING, ReportStatus.PROCESSING]),
            )
        ).scalar() or 0
        if not assigned_patient_ids:
            pending_reports = 0

        unread_alerts = self.db.execute(
            select(func.count(EmergencyAlert.id)).where(
                EmergencyAlert.patient_id.in_(assigned_patient_ids) if assigned_patient_ids else False,
                EmergencyAlert.is_acknowledged.is_(False),
            )
        ).scalar() or 0
        if not assigned_patient_ids:
            unread_alerts = 0

        recent_alerts_raw = []
        if assigned_patient_ids:
            stmt = (
                select(EmergencyAlert, Patient.full_name, Patient.phone)
                .join(Patient, EmergencyAlert.patient_id == Patient.id)
                .where(
                    EmergencyAlert.patient_id.in_(assigned_patient_ids),
                    EmergencyAlert.is_acknowledged.is_(False),
                )
                .order_by(EmergencyAlert.created_at.desc())
                .limit(10)
            )
            recent_alerts_raw = self.db.execute(stmt).all()

        recent_alerts = [
            {
                "id": str(alert.id),
                "patient_id": str(alert.patient_id),
                "patient_name": patient_name,
                "risk_level": alert.risk_level.value,
                "symptoms": alert.symptoms,
                "analysis": alert.analysis,
                "is_acknowledged": alert.is_acknowledged,
                "created_at": alert.created_at.isoformat(),
                "patient_phone": patient_phone,
            }
            for alert, patient_name, patient_phone in recent_alerts_raw
        ]

        profile = {
            "id": str(doctor.id),
            "full_name": doctor.full_name,
            "email": doctor.email,
            "specialization": doctor.specialization,
            "phone": doctor.phone,
            "hospital_name": doctor.hospital_name,
            "years_of_experience": doctor.years_of_experience,
        }

        analytics = {
            "total_patients": total_patients,
            "active_patients": active_patients,
            "total_appointments": total_appts,
            "upcoming_appointments": upcoming_appts,
            "pending_reports": pending_reports,
            "unread_alerts": unread_alerts,
            "pending_follow_ups": 0,
        }

        return {
            "doctor": profile,
            "analytics": analytics,
            "recent_alerts": recent_alerts,
        }

    def get_patients(
        self,
        doctor_id: str,
        search: Optional[str] = None,
        sort_by: str = "full_name",
        sort_order: str = "asc",
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse:
        doctor_uuid = uuid.UUID(doctor_id)
        assigned_ids = self._get_assigned_patient_ids(doctor_uuid)

        if not assigned_ids:
            return PaginatedResponse.create([], 0, page, per_page)

        patient_ids_list = list(assigned_ids)

        query = (
            select(
                Patient,
                PatientDoctor.created_at.label("assigned_at"),
            )
            .join(PatientDoctor, PatientDoctor.patient_id == Patient.id)
            .where(
                PatientDoctor.doctor_id == doctor_uuid,
                PatientDoctor.deleted_at.is_(None),
                Patient.id.in_(patient_ids_list),
            )
        )

        if search:
            pattern = f"%{search}%"
            query = query.where(
                Patient.full_name.ilike(pattern) | Patient.email.ilike(pattern)
            )

        sort_col = getattr(Patient, sort_by, Patient.full_name)
        sort_method = sort_col.asc if sort_order == "asc" else sort_col.desc
        query = query.order_by(sort_method())

        total = self.db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar() or 0

        offset = (page - 1) * per_page
        rows = self.db.execute(query.offset(offset).limit(per_page)).all()

        patient_ids = [row.Patient.id for row in rows]
        pid_set = [str(p) for p in patient_ids]

        medicines_count = {}
        appointments_count = {}
        alerts_count = {}
        adherence_rates = {}
        last_active_map = {}

        if pid_set:
            pid_uuids = [uuid.UUID(p) for p in pid_set]

            med_counts = self.db.execute(
                select(
                    Medicine.patient_id,
                    func.count(Medicine.id),
                ).where(
                    Medicine.patient_id.in_(pid_uuids),
                    Medicine.is_active.is_(True),
                    Medicine.deleted_at.is_(None),
                ).group_by(Medicine.patient_id)
            ).all()
            medicines_count = {str(row[0]): row[1] for row in med_counts}

            appt_counts = self.db.execute(
                select(
                    Appointment.patient_id,
                    func.count(Appointment.id),
                ).where(
                    Appointment.patient_id.in_(pid_uuids),
                    Appointment.deleted_at.is_(None),
                ).group_by(Appointment.patient_id)
            ).all()
            appointments_count = {str(row[0]): row[1] for row in appt_counts}

            alert_counts = self.db.execute(
                select(
                    EmergencyAlert.patient_id,
                    func.count(EmergencyAlert.id),
                ).where(
                    EmergencyAlert.patient_id.in_(pid_uuids),
                    EmergencyAlert.is_acknowledged.is_(False),
                ).group_by(EmergencyAlert.patient_id)
            ).all()
            alerts_count = {str(row[0]): row[1] for row in alert_counts}

            adherence_data = self.db.execute(
                select(
                    AdherenceLog.patient_id,
                    func.count(AdherenceLog.id),
                    func.sum(
                        case((AdherenceLog.status == AdherenceStatus.TAKEN, 1), else_=0)
                    ),
                ).where(
                    AdherenceLog.patient_id.in_(pid_uuids),
                ).group_by(AdherenceLog.patient_id)
            ).all()
            for pid, total_doses, taken_doses in adherence_data:
                pid_str = str(pid)
                if total_doses and total_doses > 0:
                    adherence_rates[pid_str] = round(taken_doses / total_doses * 100, 1)
                else:
                    adherence_rates[pid_str] = None

            last_active = self.db.execute(
                select(
                    ChatHistory.patient_id,
                    func.max(ChatHistory.created_at),
                ).where(
                    ChatHistory.patient_id.in_(pid_uuids),
                ).group_by(ChatHistory.patient_id)
            ).all()
            last_active_map = {str(row[0]): row[1] for row in last_active}

        items = []
        for row in rows:
            p = row.Patient
            pid_str = str(p.id)
            items.append({
                "id": pid_str,
                "full_name": p.full_name,
                "email": p.email,
                "phone": p.phone,
                "gender": p.gender.value if p.gender else None,
                "blood_group": p.blood_group.value if p.blood_group else None,
                "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else None,
                "active_medicines_count": medicines_count.get(pid_str, 0),
                "upcoming_appointments_count": appointments_count.get(pid_str, 0),
                "pending_alerts_count": alerts_count.get(pid_str, 0),
                "last_active": last_active_map.get(pid_str),
                "overall_adherence_rate": adherence_rates.get(pid_str),
                "assigned_at": row.assigned_at,
            })

        return PaginatedResponse.create(items, total, page, per_page)

    def get_appointments(
        self,
        doctor_id: str,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse:
        doctor_uuid = uuid.UUID(doctor_id)

        query = (
            select(Appointment, Patient.full_name, Patient.phone, Patient.date_of_birth)
            .join(Patient, Appointment.patient_id == Patient.id)
            .where(
                Appointment.doctor_id == doctor_uuid,
                Appointment.deleted_at.is_(None),
            )
        )

        if status:
            try:
                status_enum = AppointmentStatus(status)
                query = query.where(Appointment.status == status_enum)
            except ValueError:
                pass

        query = query.order_by(Appointment.scheduled_at.desc())

        total = self.db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar() or 0

        offset = (page - 1) * per_page
        rows = self.db.execute(query.offset(offset).limit(per_page)).all()

        items = []
        for appt, patient_name, patient_phone, patient_dob in rows:
            items.append({
                "id": str(appt.id),
                "patient_id": str(appt.patient_id),
                "patient_name": patient_name,
                "title": appt.title,
                "description": appt.description,
                "scheduled_at": appt.scheduled_at.isoformat(),
                "status": appt.status.value,
                "patient_phone": patient_phone,
                "patient_dob": patient_dob.isoformat() if patient_dob else None,
                "created_at": appt.created_at.isoformat(),
            })

        return PaginatedResponse.create(items, total, page, per_page)

    def get_pending_reports(
        self,
        doctor_id: str,
        status_filter: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse:
        doctor_uuid = uuid.UUID(doctor_id)
        assigned_ids = self._get_assigned_patient_ids(doctor_uuid)

        if not assigned_ids:
            return PaginatedResponse.create([], 0, page, per_page)

        query = (
            select(Report, Patient.full_name)
            .join(Patient, Report.patient_id == Patient.id)
            .where(Report.patient_id.in_(list(assigned_ids)))
        )

        if status_filter:
            try:
                status_enum = ReportStatus(status_filter)
                query = query.where(Report.status == status_enum)
            except ValueError:
                pass
        else:
            query = query.where(
                Report.status.in_([ReportStatus.PENDING, ReportStatus.PROCESSING])
            )

        query = query.order_by(Report.uploaded_at.desc())

        total = self.db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar() or 0

        offset = (page - 1) * per_page
        rows = self.db.execute(query.offset(offset).limit(per_page)).all()

        items = []
        for report, patient_name in rows:
            med_count = self.db.execute(
                select(func.count(Medicine.id)).where(
                    Medicine.report_id == report.id,
                    Medicine.deleted_at.is_(None),
                )
            ).scalar() or 0

            items.append({
                "id": str(report.id),
                "patient_id": str(report.patient_id),
                "patient_name": patient_name,
                "title": report.title,
                "file_type": report.file_type,
                "status": report.status.value,
                "uploaded_at": report.uploaded_at.isoformat(),
                "processed_at": report.processed_at.isoformat() if report.processed_at else None,
                "medicine_count": med_count,
                "doctor_id": str(report.doctor_id) if report.doctor_id else None,
            })

        return PaginatedResponse.create(items, total, page, per_page)

    def get_ai_summaries(
        self,
        doctor_id: str,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse:
        doctor_uuid = uuid.UUID(doctor_id)
        assigned_ids = self._get_assigned_patient_ids(doctor_uuid)

        if not assigned_ids:
            return PaginatedResponse.create([], 0, page, per_page)

        pid_uuids = list(assigned_ids)

        patients = self.db.execute(
            select(Patient).where(Patient.id.in_(pid_uuids))
        ).scalars().all()

        items = []
        for p in patients:
            pid = p.id

            med_count = self.db.execute(
                select(func.count(Medicine.id)).where(
                    Medicine.patient_id == pid,
                    Medicine.is_active.is_(True),
                    Medicine.deleted_at.is_(None),
                )
            ).scalar() or 0

            adherence_data = self.db.execute(
                select(
                    func.count(AdherenceLog.id),
                    func.sum(
                        case((AdherenceLog.status == AdherenceStatus.TAKEN, 1), else_=0)
                    ),
                ).where(AdherenceLog.patient_id == pid)
            ).one()
            total_doses, taken_doses = adherence_data
            adherence_rate = round(taken_doses / total_doses * 100, 1) if total_doses and total_doses > 0 else 0.0

            alert_count = self.db.execute(
                select(func.count(EmergencyAlert.id)).where(
                    EmergencyAlert.patient_id == pid,
                    EmergencyAlert.is_acknowledged.is_(False),
                )
            ).scalar() or 0

            highest_alert = self.db.execute(
                select(EmergencyAlert.symptoms).where(
                    EmergencyAlert.patient_id == pid,
                    EmergencyAlert.risk_level == RiskLevel.HIGH,
                    EmergencyAlert.is_acknowledged.is_(False),
                ).limit(1)
            ).scalar()

            last_chat = self.db.execute(
                select(ChatHistory.created_at).where(
                    ChatHistory.patient_id == pid,
                ).order_by(ChatHistory.created_at.desc()).limit(1)
            ).scalar()

            items.append({
                "patient_id": str(pid),
                "patient_name": p.full_name,
                "overall_adherence_rate": adherence_rate,
                "alert_count": alert_count,
                "highest_risk_alert": highest_alert,
                "generated_at": last_chat.isoformat() if last_chat else None,
                "medicines_count": med_count,
                "recent_symptoms": [],
            })

        items.sort(key=lambda x: x["alert_count"], reverse=True)

        total = len(items)
        offset = (page - 1) * per_page
        page_items = items[offset : offset + per_page]

        return PaginatedResponse.create(page_items, total, page, per_page)

    def get_alerts(
        self,
        doctor_id: str,
        risk_level: Optional[str] = None,
        is_acknowledged: Optional[bool] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> PaginatedResponse:
        doctor_uuid = uuid.UUID(doctor_id)
        assigned_ids = self._get_assigned_patient_ids(doctor_uuid)

        if not assigned_ids:
            return PaginatedResponse.create([], 0, page, per_page)

        query = (
            select(EmergencyAlert, Patient.full_name, Patient.phone)
            .join(Patient, EmergencyAlert.patient_id == Patient.id)
            .where(EmergencyAlert.patient_id.in_(list(assigned_ids)))
        )

        if risk_level:
            try:
                rl = RiskLevel(risk_level)
                query = query.where(EmergencyAlert.risk_level == rl)
            except ValueError:
                pass

        if is_acknowledged is not None:
            query = query.where(EmergencyAlert.is_acknowledged.is_(is_acknowledged))

        query = query.order_by(
            case(
                (EmergencyAlert.risk_level == RiskLevel.HIGH, 0),
                (EmergencyAlert.risk_level == RiskLevel.MEDIUM, 1),
                else_=2,
            ),
            EmergencyAlert.created_at.desc(),
        )

        total = self.db.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar() or 0

        offset = (page - 1) * per_page
        rows = self.db.execute(query.offset(offset).limit(per_page)).all()

        items = []
        for alert, patient_name, patient_phone in rows:
            items.append({
                "id": str(alert.id),
                "patient_id": str(alert.patient_id),
                "patient_name": patient_name,
                "risk_level": alert.risk_level.value,
                "symptoms": alert.symptoms,
                "analysis": alert.analysis,
                "is_acknowledged": alert.is_acknowledged,
                "created_at": alert.created_at.isoformat(),
                "patient_phone": patient_phone,
            })

        return PaginatedResponse.create(items, total, page, per_page)

    def _get_assigned_patient_ids(self, doctor_uuid: uuid.UUID) -> set[uuid.UUID]:
        rows = self.db.execute(
            select(PatientDoctor.patient_id).where(
                PatientDoctor.doctor_id == doctor_uuid,
                PatientDoctor.deleted_at.is_(None),
            )
        ).all()
        return {row[0] for row in rows}
