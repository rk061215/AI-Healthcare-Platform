from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.auth import (
    AuthResponse,
    DoctorRegisterRequest,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    PatientRegisterRequest,
    RefreshResponse,
    RefreshTokenRequest,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register/patient",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient",
)
def register_patient(
    request: PatientRegisterRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    return service.register_patient(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        phone=request.phone,
        date_of_birth=request.date_of_birth,
        gender=request.gender,
        terms_accepted=request.terms_accepted,
    )


@router.post(
    "/register/doctor",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new doctor",
)
def register_doctor(
    request: DoctorRegisterRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    return service.register_doctor(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        phone=request.phone,
        license_number=request.license_number,
        hospital_name=request.hospital_name,
        specialization=request.specialization,
        years_of_experience=request.years_of_experience,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email, password, and role",
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    return service.login(
        email=request.email,
        password=request.password,
        role=request.role,
        remember_me=request.remember_me,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout and revoke refresh token",
)
def logout(
    request: LogoutRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    service.logout(request.refresh_token)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Refresh access and refresh tokens",
)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    result = service.refresh(request.refresh_token)
    return result


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current authenticated user profile",
)
def get_me(
    payload: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    user_data = service.get_current_user(payload["sub"], payload["role"])
    return user_data
