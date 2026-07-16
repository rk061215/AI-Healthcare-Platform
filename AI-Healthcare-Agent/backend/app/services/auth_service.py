import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import (
    ConflictException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.core.security import (
    create_token_pair,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.refresh_token import RefreshToken
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.patient_repo = PatientRepository(db)
        self.doctor_repo = DoctorRepository(db)
        self.refresh_token_repo = RefreshTokenRepository(db)

    def register_patient(
        self,
        email: str,
        password: str,
        full_name: str,
        phone: str | None = None,
        date_of_birth: str | None = None,
        gender: str | None = None,
        terms_accepted: bool = False,
    ) -> dict:
        existing = self.patient_repo.get_by_email(email)
        if existing:
            raise ConflictException("A patient with this email already exists")

        patient = Patient(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            phone=phone,
            gender=gender,
            terms_accepted=terms_accepted,
            terms_accepted_at=datetime.now(timezone.utc) if terms_accepted else None,
        )
        if date_of_birth:
            from datetime import date
            patient.date_of_birth = date.fromisoformat(date_of_birth)

        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)

        tokens = create_token_pair(str(patient.id), "patient")
        self._store_refresh_token(
            jti=tokens["refresh_jti"],
            token_hash=hash_token(tokens["refresh_token"]),
            user_id=str(patient.id),
            role="patient",
            expires_at=tokens["refresh_expires_at"],
        )

        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens["expires_in"],
            "user": {
                "id": str(patient.id),
                "email": patient.email,
                "full_name": patient.full_name,
                "role": "patient",
                "phone": patient.phone,
            },
        }

    def register_doctor(
        self,
        email: str,
        password: str,
        full_name: str,
        phone: str | None = None,
        license_number: str | None = None,
        hospital_name: str | None = None,
        specialization: str | None = None,
        years_of_experience: int | None = None,
    ) -> dict:
        existing = self.doctor_repo.get_by_email(email)
        if existing:
            raise ConflictException("A doctor with this email already exists")

        doctor = Doctor(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            phone=phone,
            license_number=license_number,
            hospital_name=hospital_name,
            specialization=specialization,
            years_of_experience=years_of_experience,
        )
        self.db.add(doctor)
        self.db.commit()
        self.db.refresh(doctor)

        tokens = create_token_pair(str(doctor.id), "doctor")
        self._store_refresh_token(
            jti=tokens["refresh_jti"],
            token_hash=hash_token(tokens["refresh_token"]),
            user_id=str(doctor.id),
            role="doctor",
            expires_at=tokens["refresh_expires_at"],
        )

        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens["expires_in"],
            "user": {
                "id": str(doctor.id),
                "email": doctor.email,
                "full_name": doctor.full_name,
                "role": "doctor",
                "phone": doctor.phone,
                "specialization": doctor.specialization,
                "license_number": doctor.license_number,
                "hospital_name": doctor.hospital_name,
                "years_of_experience": doctor.years_of_experience,
            },
        }

    def login(self, email: str, password: str, role: str, remember_me: bool = False) -> dict:
        user = None
        if role == "patient":
            user = self.patient_repo.get_by_email(email)
        elif role == "doctor":
            user = self.doctor_repo.get_by_email(email)

        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("Account is deactivated. Contact support.")

        tokens = create_token_pair(str(user.id), role, remember_me)
        self._store_refresh_token(
            jti=tokens["refresh_jti"],
            token_hash=hash_token(tokens["refresh_token"]),
            user_id=str(user.id),
            role=role,
            expires_at=tokens["refresh_expires_at"],
        )

        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens["expires_in"],
            "user": self._build_user_response(user, role),
        }

    def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            raise UnauthorizedException("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")

        jti = payload.get("jti")
        stored = self.refresh_token_repo.get_by_jti(jti)
        if not stored:
            raise NotFoundException("Refresh token")

        if stored.is_revoked:
            raise UnauthorizedException("Token already revoked")

        self.refresh_token_repo.revoke_token(jti)

    def refresh(self, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
        except ValueError:
            raise UnauthorizedException("Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise UnauthorizedException("Invalid token type")

        jti = payload.get("jti")
        user_id = payload.get("sub")
        role = payload.get("role")

        stored = self.refresh_token_repo.get_by_jti(jti)
        if not stored:
            raise UnauthorizedException("Refresh token not found")

        if stored.is_revoked:
            raise UnauthorizedException("Refresh token has been revoked")

        token_hash = hash_token(refresh_token)
        if stored.token_hash != token_hash:
            self.refresh_token_repo.revoke_token(jti)
            raise UnauthorizedException("Refresh token mismatch")

        self.refresh_token_repo.revoke_token(jti)

        tokens = create_token_pair(user_id, role)
        self._store_refresh_token(
            jti=tokens["refresh_jti"],
            token_hash=hash_token(tokens["refresh_token"]),
            user_id=user_id,
            role=role,
            expires_at=tokens["refresh_expires_at"],
        )

        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens["expires_in"],
        }

    def get_current_user(self, user_id: str, role: str) -> dict:
        user = None
        if role == "patient":
            user = self.patient_repo.get(user_id)
        elif role == "doctor":
            user = self.doctor_repo.get(user_id)

        if not user:
            raise NotFoundException(f"{role.capitalize()}", user_id)

        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        return self._build_user_response(user, role)

    def _store_refresh_token(
        self,
        jti: str,
        token_hash: str,
        user_id: str,
        role: str,
        expires_at: datetime,
    ) -> RefreshToken:
        token = RefreshToken(
            jti=jti,
            token_hash=token_hash,
            user_id=uuid.UUID(user_id),
            role=role,
            expires_at=expires_at,
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def _build_user_response(self, user: Patient | Doctor, role: str) -> dict:
        if role == "patient":
            return {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": "patient",
                "phone": user.phone,
                "date_of_birth": str(user.date_of_birth) if user.date_of_birth else None,
                "gender": user.gender,
                "is_active": user.is_active,
            }
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": "doctor",
            "phone": user.phone,
            "specialization": user.specialization,
            "license_number": user.license_number,
            "hospital_name": user.hospital_name,
            "years_of_experience": user.years_of_experience,
            "is_active": user.is_active,
        }
