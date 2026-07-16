import time

from loguru import logger
from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.metrics import metrics as app_metrics

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency (seconds)",
    ["method", "path"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_flight = Gauge(
    "http_requests_in_flight",
    "Current in-flight HTTP requests",
    ["method", "path"],
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request body size (bytes)",
    ["method", "path"],
    buckets=(256, 1024, 4096, 16384, 65536, 262144, 1048576),
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response body size (bytes)",
    ["method", "path"],
    buckets=(256, 1024, 4096, 16384, 65536, 262144, 1048576),
)


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        logger.debug("MetricsMiddleware initialized")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path
        method = request.method

        if path in ("/metrics", "/live", "/ready", "/health"):
            return await call_next(request)

        http_requests_in_flight.labels(method=method, path=path).inc()

        start_time = time.perf_counter()

        try:
            response = await call_next(request)

            status_code = response.status_code
            duration = time.perf_counter() - start_time

            http_requests_total.labels(method=method, path=path, status=status_code).inc()
            http_request_duration_seconds.labels(method=method, path=path).observe(duration)

            content_length = response.headers.get("content-length")
            if content_length:
                http_response_size_bytes.labels(method=method, path=path).observe(
                    int(content_length)
                )

            app_metrics.increment("http.requests", {"method": method, "path": path, "status": str(status_code)})
            app_metrics.record_latency("http.request_duration", duration * 1000, {"method": method, "path": path})
            if 400 <= status_code < 600:
                category = "4xx" if status_code < 500 else "5xx"
                app_metrics.record_error("http.errors", category, {"method": method, "path": path, "status": str(status_code)})

            return response
        finally:
            http_requests_in_flight.labels(method=method, path=path).dec()
