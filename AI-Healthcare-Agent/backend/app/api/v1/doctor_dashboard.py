from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_doctor, get_db
from app.services.doctor_dashboard_service import DoctorDashboardService

router = APIRouter()


@router.get("/overview")
def get_overview(
    payload: dict = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    service = DoctorDashboardService(db)
    return service.get_overview(payload["sub"])


@router.get("/patients")
def get_patients(
    search: Optional[str] = Query(None, max_length=100),
    sort_by: str = Query("full_name", pattern="^(full_name|email|created_at)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1, le=1000),
    per_page: int = Query(20, ge=1, le=100),
    payload: dict = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    service = DoctorDashboardService(db)
    return service.get_patients(
        payload["sub"],
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page,
    )


@router.get("/appointments")
def get_appointments(
    status: Optional[str] = Query(None, max_length=50),
    page: int = Query(1, ge=1, le=1000),
    per_page: int = Query(20, ge=1, le=100),
    payload: dict = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    service = DoctorDashboardService(db)
    return service.get_appointments(
        payload["sub"],
        status=status,
        page=page,
        per_page=per_page,
    )


@router.get("/reports")
def get_reports(
    status: Optional[str] = Query(None, max_length=50),
    page: int = Query(1, ge=1, le=1000),
    per_page: int = Query(20, ge=1, le=100),
    payload: dict = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    service = DoctorDashboardService(db)
    return service.get_pending_reports(
        payload["sub"],
        status_filter=status,
        page=page,
        per_page=per_page,
    )


@router.get("/summaries")
def get_summaries(
    page: int = Query(1, ge=1, le=1000),
    per_page: int = Query(20, ge=1, le=100),
    payload: dict = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    service = DoctorDashboardService(db)
    return service.get_ai_summaries(
        payload["sub"],
        page=page,
        per_page=per_page,
    )


@router.get("/alerts")
def get_alerts(
    risk_level: Optional[str] = Query(None, max_length=20),
    is_acknowledged: Optional[bool] = Query(None),
    page: int = Query(1, ge=1, le=1000),
    per_page: int = Query(20, ge=1, le=100),
    payload: dict = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    service = DoctorDashboardService(db)
    return service.get_alerts(
        payload["sub"],
        risk_level=risk_level,
        is_acknowledged=is_acknowledged,
        page=page,
        per_page=per_page,
    )
