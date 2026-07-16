import re
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class TokenPayload(BaseModel):
    sub: str
    role: str
    exp: int
    iat: int
    type: str
    jti: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    phone: Optional[str] = None


class PatientUserResponse(UserResponse):
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    is_active: bool = True


class DoctorUserResponse(UserResponse):
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    hospital_name: Optional[str] = None
    years_of_experience: Optional[int] = None


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    hospital_name: Optional[str] = None
    years_of_experience: Optional[int] = None
    is_active: bool = True


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str = Field(default="patient", pattern="^(patient|doctor)$")
    remember_me: bool = False


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?])"
)


def validate_password(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(password) > 128:
        raise ValueError("Password must be at most 128 characters long")
    if not PASSWORD_REGEX.match(password):
        raise ValueError(
            "Password must contain at least one uppercase letter, "
            "one lowercase letter, one number, and one special character"
        )
    return password


PHONE_REGEX = re.compile(r"^\+?[1-9]\d{1,14}$")


def validate_phone(phone: str) -> str:
    if not PHONE_REGEX.match(phone):
        raise ValueError("Invalid phone number format (E.164 format required)")
    return phone


class PatientRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str
    full_name: str = Field(min_length=1, max_length=255)
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    terms_accepted: bool = False

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return validate_password(v)

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, v: str) -> str:
        return v  # Will be checked at model level

    @field_validator("phone")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_phone(v)
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_lower = v.lower()
            allowed = {"male", "female", "other", "prefer_not_to_say"}
            if v_lower not in allowed:
                raise ValueError(f"Gender must be one of: {', '.join(allowed)}")
            return v_lower
        return v

    @field_validator("terms_accepted")
    @classmethod
    def validate_terms(cls, v: bool) -> bool:
        if not v:
            raise ValueError("You must accept the terms and conditions")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                parsed = date.fromisoformat(v)
                if parsed >= date.today():
                    raise ValueError("Date of birth must be in the past")
            except ValueError as e:
                if "must be in the past" in str(e):
                    raise
                raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class DoctorRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str
    full_name: str = Field(min_length=1, max_length=255)
    phone: Optional[str] = None
    license_number: Optional[str] = None
    hospital_name: Optional[str] = None
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = None

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        return validate_password(v)

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, v: str) -> str:
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return validate_phone(v)
        return v

    @field_validator("years_of_experience")
    @classmethod
    def validate_experience(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v < 0:
                raise ValueError("Years of experience cannot be negative")
            if v > 70:
                raise ValueError("Years of experience seems unrealistic")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return validate_password(v)
