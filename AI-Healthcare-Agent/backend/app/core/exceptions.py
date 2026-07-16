from typing import Any, Optional


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, entity: str, entity_id: Optional[str] = None):
        message = f"{entity} not found"
        if entity_id:
            message += f": {entity_id}"
        super().__init__(message=message, status_code=404)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message=message, status_code=401)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Access denied"):
        super().__init__(message=message, status_code=403)


class ConflictException(AppException):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=409)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation failed", detail: Optional[Any] = None):
        super().__init__(message=message, status_code=422, detail=detail)


class RateLimitException(AppException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message=message, status_code=429)
