from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_patient, get_db
from app.schemas.dashboard import (
    AIStatusCard,
    AppointmentSummary,
    DashboardOverview,
    MedicineWithSchedule,
    ReminderHistoryItem,
    ReportSummary,
    TimelineEvent,
    TodayScheduleItem,
)
from app.schemas.pagination import PaginatedResponse
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_overview(payload["sub"])


@router.get("/medicines")
def get_dashboard_medicines(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_medicines(payload["sub"], page=page, per_page=per_page)


@router.get("/appointments")
def get_dashboard_appointments(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    status: str | None = Query(None),
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_appointments(
        payload["sub"], page=page, per_page=per_page, status_filter=status
    )


@router.get("/reports")
def get_dashboard_reports(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    status: str | None = Query(None),
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_reports(
        payload["sub"], page=page, per_page=per_page, status_filter=status
    )


@router.get("/schedule", response_model=list[TodayScheduleItem])
def get_today_schedule(
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_today_schedule(payload["sub"])


@router.get("/timeline", response_model=list[TimelineEvent])
def get_health_timeline(
    days: int = Query(30, ge=1, le=365),
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_timeline(payload["sub"], days=days)


@router.get("/reminders")
def get_reminder_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_reminder_history(payload["sub"], page=page, per_page=per_page)


@router.get("/ai-status", response_model=AIStatusCard)
def get_ai_status(
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = DashboardService(db)
    return service.get_ai_status(payload["sub"])
