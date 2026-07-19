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
from app.core.trace import probe
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
        probe("register_patient: checking duplicate email")
        existing = self.patient_repo.get_by_email(email)
        if existing:
            probe("register_patient: duplicate email found")
            raise ConflictException("A patient with this email already exists")
        probe("register_patient: email is unique")

        probe("register_patient: hashing password")
        hashed = hash_password(password)
        probe("register_patient: password hashed successfully")

        probe("register_patient: creating Patient model instance")
        patient = Patient(
            email=email,
            password_hash=hashed,
            full_name=full_name,
            phone=phone,
            gender=gender,
            terms_accepted=terms_accepted,
            terms_accepted_at=datetime.now(timezone.utc) if terms_accepted else None,
        )
        if date_of_birth:
            from datetime import date
            patient.date_of_birth = date.fromisoformat(date_of_birth)
        probe("register_patient: Patient model created")

        probe("register_patient: db.add(patient)")
        self.db.add(patient)

        probe("register_patient: db.commit()")
        self.db.commit()
        probe("register_patient: db.commit() succeeded")

        probe("register_patient: db.refresh(patient)")
        self.db.refresh(patient)
        probe(f"register_patient: patient.id={patient.id}")

        probe("register_patient: creating token pair")
        tokens = create_token_pair(str(patient.id), "patient")
        probe("register_patient: token pair created")

        probe("register_patient: storing refresh token")
        self._store_refresh_token(
            jti=tokens["refresh_jti"],
            token_hash=hash_token(tokens["refresh_token"]),
            user_id=str(patient.id),
            role="patient",
            expires_at=tokens["refresh_expires_at"],
        )
        probe("register_patient: refresh token stored")

        result = {
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
        probe("register_patient: returning response successfully")
        return result

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
        probe("register_doctor: checking duplicate email")
        existing = self.doctor_repo.get_by_email(email)
        if existing:
            probe("register_doctor: duplicate email found")
            raise ConflictException("A doctor with this email already exists")
        probe("register_doctor: email is unique")

        probe("register_doctor: hashing password")
        hashed = hash_password(password)
        probe("register_doctor: password hashed successfully")

        probe("register_doctor: creating Doctor model instance")
        doctor = Doctor(
            email=email,
            password_hash=hashed,
            full_name=full_name,
            phone=phone,
            license_number=license_number,
            hospital_name=hospital_name,
            specialization=specialization,
            years_of_experience=years_of_experience,
        )
        probe("register_doctor: Doctor model created")

        probe("register_doctor: db.add(doctor)")
        self.db.add(doctor)

        probe("register_doctor: db.commit()")
        self.db.commit()
        probe("register_doctor: db.commit() succeeded")

        probe("register_doctor: db.refresh(doctor)")
        self.db.refresh(doctor)
        probe(f"register_doctor: doctor.id={doctor.id}")

        probe("register_doctor: creating token pair")
        tokens = create_token_pair(str(doctor.id), "doctor")
        probe("register_doctor: token pair created")

        probe("register_doctor: storing refresh token")
        self._store_refresh_token(
            jti=tokens["refresh_jti"],
            token_hash=hash_token(tokens["refresh_token"]),
            user_id=str(doctor.id),
            role="doctor",
            expires_at=tokens["refresh_expires_at"],
        )
        probe("register_doctor: refresh token stored")

        result = {
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
        probe("register_doctor: returning response successfully")
        return result

    def login(self, email: str, password: str, role: str, remember_me: bool = False) -> dict:
        probe(f"login: looking up {role} by email")
        user = None
        if role == "patient":
            user = self.patient_repo.get_by_email(email)
        elif role == "doctor":
            user = self.doctor_repo.get_by_email(email)

        probe("login: verifying password")
        if not user or not verify_password(password, user.password_hash):
            probe("login: invalid email or password")
            raise UnauthorizedException("Invalid email or password")
        probe("login: password verified")

        if not user.is_active:
            probe("login: account deactivated")
            raise UnauthorizedException("Account is deactivated. Contact support.")
        probe("login: account is active")

        probe("login: creating token pair")
        tokens = create_token_pair(str(user.id), role, remember_me)
        probe("login: token pair created")

        probe("login: storing refresh token")
        self._store_refresh_token(
            jti=tokens["refresh_jti"],
            token_hash=hash_token(tokens["refresh_token"]),
            user_id=str(user.id),
            role=role,
            expires_at=tokens["refresh_expires_at"],
        )
        probe("login: refresh token stored")

        result = {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens["expires_in"],
            "user": self._build_user_response(user, role),
        }
        probe("login: returning response successfully")
        return result

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
        probe("refresh: decoding token")
        try:
            payload = decode_token(refresh_token)
        except ValueError as e:
            probe(f"refresh: decode failed - {e}")
            raise UnauthorizedException("Invalid or expired refresh token")
        probe("refresh: token decoded")

        if payload.get("type") != "refresh":
            probe("refresh: invalid token type")
            raise UnauthorizedException("Invalid token type")
        probe("refresh: token type is refresh")

        jti = payload.get("jti")
        user_id = payload.get("sub")
        role = payload.get("role")

        probe(f"refresh: looking up jti={jti}")
        stored = self.refresh_token_repo.get_by_jti(jti)
        if not stored:
            probe("refresh: token not found")
            raise UnauthorizedException("Refresh token not found")
        probe("refresh: token found")

        if stored.is_revoked:
            probe("refresh: token already revoked")
            raise UnauthorizedException("Refresh token has been revoked")
        probe("refresh: token not revoked")

        probe("refresh: verifying hash")
        token_hash = hash_token(refresh_token)
        if stored.token_hash != token_hash:
            probe("refresh: hash mismatch - revoking")
            self.refresh_token_repo.revoke_token(jti)
            raise UnauthorizedException("Refresh token mismatch")
        probe("refresh: hash verified")

        probe("refresh: revoking old token")
        self.refresh_token_repo.revoke_token(jti)
        probe("refresh: old token revoked")

        probe("refresh: creating new token pair")
        tokens = create_token_pair(user_id, role)
        probe("refresh: new token pair created")

        probe("refresh: storing new refresh token")
        self._store_refresh_token(
            jti=tokens["refresh_jti"],
            token_hash=hash_token(tokens["refresh_token"]),
            user_id=user_id,
            role=role,
            expires_at=tokens["refresh_expires_at"],
        )
        probe("refresh: new refresh token stored")

        result = {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens["expires_in"],
        }
        probe("refresh: returning response successfully")
        return result

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
