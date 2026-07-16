from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_doctor, get_current_patient, get_current_user, get_db
from app.schemas.appointment import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentResponse,
    AppointmentUpdate,
    RecurringAppointmentCreate,
)
from app.services.appointment_service import AppointmentService

router = APIRouter()


@router.post("", response_model=AppointmentResponse)
def create_appointment(
    data: AppointmentCreate,
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.create_appointment(
        data.model_dump(),
        user_id=payload["sub"],
        role=payload["role"],
    )


@router.get("")
def list_appointments(
    status: Optional[str] = Query(None, max_length=50),
    page: int = Query(1, ge=1, le=1000),
    per_page: int = Query(20, ge=1, le=100),
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.list_appointments(
        payload["sub"],
        payload["role"],
        status=status,
        page=page,
        per_page=per_page,
    )


@router.get("/{appointment_id}")
def get_appointment(
    appointment_id: str,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.get_appointment(
        appointment_id,
        user_id=payload["sub"],
        role=payload["role"],
    )


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: str,
    data: AppointmentUpdate,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.update_appointment(
        appointment_id,
        data.model_dump(exclude_unset=True),
        user_id=payload["sub"],
        role=payload["role"],
    )


@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: str,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    service.delete_appointment(
        appointment_id,
        user_id=payload["sub"],
        role=payload["role"],
    )
    return {"message": "Appointment deleted"}


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: str,
    data: AppointmentCancel,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.cancel_appointment(
        appointment_id,
        reason=data.reason,
        user_id=payload["sub"],
        role=payload["role"],
    )


@router.post("/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    appointment_id: str,
    data: AppointmentReschedule,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.reschedule_appointment(
        appointment_id,
        scheduled_at=data.scheduled_at,
        reason=data.reason,
        user_id=payload["sub"],
        role=payload["role"],
    )


@router.post("/{appointment_id}/confirm", response_model=AppointmentResponse)
def confirm_appointment(
    appointment_id: str,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.confirm_appointment(
        appointment_id,
        user_id=payload["sub"],
        role=payload["role"],
    )


@router.post("/{appointment_id}/complete", response_model=AppointmentResponse)
def complete_appointment(
    appointment_id: str,
    follow_up_notes: Optional[str] = Query(None, max_length=1000),
    payload: dict = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.complete_appointment(
        appointment_id,
        follow_up_notes=follow_up_notes,
        user_id=payload["sub"],
        role=payload["role"],
    )


@router.post("/recurring")
def create_recurring_appointment(
    data: RecurringAppointmentCreate,
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    appointments = service.create_recurring_appointment(
        data.model_dump(),
        user_id=payload["sub"],
        role=payload["role"],
    )
    return [
        {
            "id": str(a.id),
            "patient_id": str(a.patient_id),
            "doctor_id": str(a.doctor_id),
            "title": a.title,
            "scheduled_at": a.scheduled_at.isoformat(),
            "duration_minutes": a.duration_minutes,
            "status": a.status.value,
            "timezone": a.timezone,
        }
        for a in appointments
    ]


@router.get("/{appointment_id}/audit")
def get_appointment_audit(
    appointment_id: str,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.get_audit_logs(
        appointment_id,
        user_id=payload["sub"],
        role=payload["role"],
    )


@router.get("/{appointment_id}/remind")
def send_reminder(
    appointment_id: str,
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    service.send_reminder(appointment_id)
    return {"message": "Reminder sent"}


@router.get("/doctor/slots")
def get_doctor_availability(
    payload: dict = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.get_availability(payload["sub"])


@router.post("/doctor/slots")
def set_doctor_availability(
    slots: list[dict],
    payload: dict = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.set_availability(payload["sub"], slots)


@router.get("/doctor/available-slots")
def get_available_slots(
    doctor_id: str = Query(...),
    date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.get_available_slots(doctor_id, date)
