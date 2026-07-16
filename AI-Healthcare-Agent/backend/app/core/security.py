import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str,
    role: str,
    remember_me: bool = False,
) -> tuple[str, str, datetime]:
    jti = str(uuid.uuid4())
    days = (
        settings.JWT_REFRESH_TOKEN_REMEMBER_ME_DAYS
        if remember_me
        else settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    expire = datetime.now(timezone.utc) + timedelta(days=days)
    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": jti,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expire


def create_token_pair(
    subject: str,
    role: str,
    remember_me: bool = False,
) -> dict[str, Any]:
    access_token = create_access_token(subject, role)
    refresh_token, jti, expires_at = create_refresh_token(subject, role, remember_me)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh_jti": jti,
        "refresh_expires_at": expires_at,
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def decode_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise ValueError("Invalid or expired token")


def verify_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    payload = decode_token(token)
    if payload.get("type") != expected_type:
        raise ValueError(f"Invalid token type. Expected {expected_type}")
    return payload
