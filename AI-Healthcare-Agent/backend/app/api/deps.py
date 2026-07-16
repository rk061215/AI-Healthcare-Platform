from collections.abc import Generator
from typing import Any, Callable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.database.session import get_db


def get_current_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is empty",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = verify_token(token, "access")
        return payload
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_patient(
    payload: dict = Depends(get_current_user),
) -> dict:
    if payload.get("role") != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only accessible to patients",
        )
    return payload


def get_current_doctor(
    payload: dict = Depends(get_current_user),
) -> dict:
    if payload.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only accessible to doctors",
        )
    return payload


def require_role(allowed_roles: list[str]) -> Callable:
    def role_checker(payload: dict = Depends(get_current_user)) -> dict:
        if payload.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of these roles: {', '.join(allowed_roles)}",
            )
        return payload

    return role_checker
