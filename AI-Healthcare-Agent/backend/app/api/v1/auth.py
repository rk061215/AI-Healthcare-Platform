import traceback

from fastapi import APIRouter, Depends, Response, status
from loguru import logger
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

_TRACE_STEPS: list[str] = []


def _probe(msg: str) -> None:
    _TRACE_STEPS.append(msg)
    logger.info(f"TRACE: {msg}")


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
    response: Response = None,
):
    _TRACE_STEPS.clear()

    _probe("Entering register_patient endpoint")
    _probe(f"email={request.email}, full_name={request.full_name}, phone={request.phone}, date_of_birth={request.date_of_birth}, gender={request.gender}, terms_accepted={request.terms_accepted}")
    try:
        service = AuthService(db)
        _probe("AuthService created")
        result = service.register_patient(
            email=request.email,
            password="***REDACTED***",
            full_name=request.full_name,
            phone=request.phone,
            date_of_birth=request.date_of_birth,
            gender=request.gender,
            terms_accepted=request.terms_accepted,
        )
        _probe("register_patient returned successfully")
        return result
    except Exception as e:
        _probe(f"EXCEPTION: {type(e).__name__}: {e}")
        _probe(f"Traceback:\n{traceback.format_exc()}")
        logger.error(f"TRACE: EXCEPTION in register_patient endpoint: {type(e).__name__}: {e}")
        logger.error(f"TRACE: Traceback:\n{traceback.format_exc()}")
        raise
    finally:
        if response is not None:
            response.headers["X-Trace-Count"] = str(len(_TRACE_STEPS))
            for i, step in enumerate(_TRACE_STEPS):
                response.headers[f"X-Trace-{i+1}"] = step


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
