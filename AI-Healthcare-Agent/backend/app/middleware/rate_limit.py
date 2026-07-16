import time
from collections import defaultdict
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.config import settings


class SlidingWindowEntry:
    def __init__(self, max_hits: int, window_seconds: int):
        self.max_hits = max_hits
        self.window_seconds = window_seconds
        self.hits: list[float] = []

    def is_allowed(self) -> tuple[bool, int]:
        now = time.time()
        cutoff = now - self.window_seconds
        self.hits = [h for h in self.hits if h > cutoff]
        if len(self.hits) >= self.max_hits:
            retry_after = int(self.hits[0] + self.window_seconds - now)
            return False, max(retry_after, 1)
        self.hits.append(now)
        return True, 0


class InMemoryRateLimiter:
    def __init__(self):
        self._stores: dict[str, dict[str, SlidingWindowEntry]] = defaultdict(dict)

    def check(self, key: str, route: str, max_hits: int, window_seconds: int) -> tuple[bool, int]:
        if route not in self._stores[key]:
            self._stores[key][route] = SlidingWindowEntry(max_hits, window_seconds)
        return self._stores[key][route].is_allowed()

    def reset(self) -> None:
        self._stores.clear()

    def check_login(self, key: str) -> tuple[bool, int]:
        return self.check(
            key,
            "login",
            settings.RATE_LIMIT_LOGIN_PER_MINUTE,
            60,
        )

    def check_global(self, key: str) -> tuple[bool, int]:
        return self.check(
            key,
            "global",
            settings.RATE_LIMIT_PER_MINUTE,
            60,
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        logger.info(
            f"Rate limiter initialized: {settings.RATE_LIMIT_PER_MINUTE}/min global, "
            f"{settings.RATE_LIMIT_LOGIN_PER_MINUTE}/min login"
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = self._get_client_ip(request)
        path = request.url.path
        method = request.method

        if method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return await call_next(request)

        if "/auth/login" in path:
            allowed, retry_after = rate_limiter.check_login(client_ip)
            if not allowed:
                logger.warning(f"Rate limit exceeded for login: {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too many login attempts. Please try again later.",
                        "retry_after": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

        allowed, retry_after = rate_limiter.check_global(client_ip)
        if not allowed:
            logger.warning(f"Rate limit exceeded: {client_ip} on {method} {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded. Please slow down.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        client_host = request.client
        if client_host:
            return client_host.host
        return "unknown"


rate_limiter = InMemoryRateLimiter()
