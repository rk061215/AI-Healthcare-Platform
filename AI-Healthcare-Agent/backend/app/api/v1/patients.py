from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_patient, get_db
from app.schemas.patient import PatientResponse, PatientUpdate
from app.services.patient_service import PatientService

router = APIRouter()


@router.get("/me", response_model=PatientResponse)
def get_my_profile(
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = PatientService(db)
    patient = service.get_patient(payload["sub"])
    return patient


@router.patch("/me", response_model=PatientResponse)
def update_my_profile(
    data: PatientUpdate,
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = PatientService(db)
    return service.update_patient(
        payload["sub"], data.model_dump(exclude_unset=True)
    )


@router.get("/me/doctors")
def get_my_doctors(
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = PatientService(db)
    doctors = service.get_patient_doctors(payload["sub"])
    return [
        {
            "id": str(d.id),
            "full_name": d.full_name,
            "specialization": d.specialization,
        }
        for d in doctors
    ]
