from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_doctor, get_db
from app.services.doctor_service import DoctorService

router = APIRouter()


@router.get("/me")
def get_my_profile(
    payload: dict = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    service = DoctorService(db)
    doctor = service.get_doctor(payload["sub"])
    return {
        "id": str(doctor.id),
        "email": doctor.email,
        "full_name": doctor.full_name,
        "specialization": doctor.specialization,
        "license_number": doctor.license_number,
        "phone": doctor.phone,
    }


@router.get("/me/patients")
def get_my_patients(
    payload: dict = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    service = DoctorService(db)
    patients = service.get_doctor_patients(payload["sub"])
    return [
        {
            "id": str(p.id),
            "full_name": p.full_name,
            "email": p.email,
            "phone": p.phone,
            "gender": p.gender,
            "blood_group": p.blood_group,
        }
        for p in patients
    ]


@router.post("/me/patients/{patient_id}/assign")
def assign_patient(
    patient_id: str,
    payload: dict = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    service = DoctorService(db)
    service.assign_patient(payload["sub"], patient_id)
    return {"message": "Patient assigned successfully"}
