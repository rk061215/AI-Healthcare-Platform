from opentelemetry import trace
from opentelemetry.trace import SpanKind
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.types import ASGIApp


class TracingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.tracer = trace.get_tracer(__name__)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        path = request.url.path
        method = request.method

        if path in ("/metrics", "/live", "/ready"):
            return await call_next(request)

        with self.tracer.start_as_current_span(
            f"{method} {path}",
            kind=SpanKind.SERVER,
            attributes={
                "http.method": method,
                "http.path": path,
                "request_id": getattr(request.state, "request_id", ""),
            },
        ) as span:
            response = await call_next(request)
            span.set_attribute("http.status_code", response.status_code)
            return response
