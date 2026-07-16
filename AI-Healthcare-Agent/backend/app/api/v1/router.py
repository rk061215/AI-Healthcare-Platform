from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.patients import router as patients_router
from app.api.v1.doctors import router as doctors_router
from app.api.v1.reports import router as reports_router
from app.api.v1.chat import router as chat_router
from app.api.v1.appointments import router as appointments_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.doctor_dashboard import router as doctor_dashboard_router
from app.api.v1.documents import router as documents_router
from app.api.v1.health import router as health_router
from app.api.v1.demo import router as demo_router
from app.api.v1.monitoring import router as monitoring_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(patients_router, prefix="/patients", tags=["Patients"])
api_router.include_router(doctors_router, prefix="/doctors", tags=["Doctors"])
api_router.include_router(reports_router, prefix="/reports", tags=["Reports"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(appointments_router, prefix="/appointments", tags=["Appointments"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(doctor_dashboard_router, prefix="/doctor-dashboard", tags=["Doctor Dashboard"])
api_router.include_router(demo_router, tags=["Demo"])
api_router.include_router(monitoring_router, prefix="/monitoring", tags=["Monitoring"])
