from urllib.parse import urlparse

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.config import settings


class CSRFTokenMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection via Origin / Referer header validation.

    Why this approach instead of traditional CSRF tokens:
    ----------------------------------------------------
    This application uses Bearer tokens sent in the Authorization header for
    API authentication. Browsers do NOT automatically attach Authorization
    headers to cross-origin requests — unlike cookies, which are attached
    automatically. This means the application is already inherently CSRF-safe
    when using Bearer token auth.

    However, as a defense-in-depth measure, this middleware validates that
    state-changing requests (POST, PUT, PATCH, DELETE) originate from an
    allowed origin. This prevents CSRF in scenarios where:

    1. A misconfiguration causes cookies to be used for auth
    2. A browser extension or plugin bypasses Same-Origin Policy
    3. An XSS vulnerability leaks tokens (Origin check adds a second gate)

    The Origin header is validated against the configured CORS origins.
    If Origin is not present (e.g., same-origin requests from the SPA),
    the Referer header is checked instead.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self._allowed_origins = set()
        for origin in settings.cors_origins:
            parsed = urlparse(origin)
            netloc = parsed.netloc or parsed.path
            self._allowed_origins.add(netloc)
            self._allowed_origins.add(origin)
        logger.debug(f"CSRF middleware allowed origins: {self._allowed_origins}")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return await call_next(request)

        # Skip CSRF for demo/public endpoints
        if request.url.path.startswith("/demo"):
            return await call_next(request)

        if not self._is_safe_request(request):
            logger.warning(f"CSRF check failed: {request.method} {request.url.path}")
            return JSONResponse(
                status_code=403,
                content={"error": "CSRF validation failed: invalid origin"},
            )

        return await call_next(request)

    def _is_safe_request(self, request: Request) -> bool:
        if settings.ENVIRONMENT == "development":
            return True

        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")

        if origin:
            return self._origin_is_allowed(origin)

        if referer:
            return self._origin_is_allowed(referer)

        return True

    def _origin_is_allowed(self, url: str) -> bool:
        if not url:
            return False
        for allowed in self._allowed_origins:
            if allowed in url:
                return True
        return False
