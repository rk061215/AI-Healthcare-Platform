import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from sqlalchemy import create_engine, text
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.config import settings
from app.middleware.rate_limit_base import RateLimiter


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


class PostgresRateLimiter(RateLimiter):
    def __init__(self):
        self._engine = create_engine(settings.DATABASE_URL)
        self._create_table()

    def _create_table(self) -> None:
        with self._engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    thread_id   TEXT NOT NULL,
                    route       TEXT NOT NULL,
                    hit_at      TIMESTAMP NOT NULL DEFAULT NOW()
                )
            """))
        logger.info("PostgresRateLimiter: rate_limits table ready")

    def check(self, key: str, route: str, max_hits: int, window_seconds: int) -> tuple[bool, int]:
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        with self._engine.begin() as conn:
            # Purge expired entries
            conn.execute(
                text("DELETE FROM rate_limits WHERE thread_id = :key AND route = :route AND hit_at < :cutoff"),
                {"key": key, "route": route, "cutoff": cutoff},
            )

            # Count hits within window
            row = conn.execute(
                text("SELECT COUNT(*) AS cnt FROM rate_limits WHERE thread_id = :key AND route = :route AND hit_at >= :cutoff"),
                {"key": key, "route": route, "cutoff": cutoff},
            ).one()
            count = row._mapping["cnt"]

            if count >= max_hits:
                oldest = conn.execute(
                    text("SELECT hit_at FROM rate_limits WHERE thread_id = :key AND route = :route AND hit_at >= :cutoff ORDER BY hit_at ASC LIMIT 1"),
                    {"key": key, "route": route, "cutoff": cutoff},
                ).scalar()
                retry_after = int((oldest + timedelta(seconds=window_seconds) - datetime.utcnow()).total_seconds())
                return False, max(retry_after, 1)

            conn.execute(
                text("INSERT INTO rate_limits (thread_id, route, hit_at) VALUES (:key, :route, NOW())"),
                {"key": key, "route": route},
            )
        return True, 0

    def reset(self) -> None:
        with self._engine.begin() as conn:
            conn.execute(text("DELETE FROM rate_limits"))

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


class RateLimiterFactory:
    @staticmethod
    def create() -> RateLimiter:
        provider = settings.RATE_LIMIT_PROVIDER
        if provider == "postgres":
            logger.info("RateLimiterFactory: creating PostgresRateLimiter")
            return PostgresRateLimiter()
        logger.info("RateLimiterFactory: creating InMemoryRateLimiter")
        return InMemoryRateLimiter()


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


rate_limiter = RateLimiterFactory.create()
