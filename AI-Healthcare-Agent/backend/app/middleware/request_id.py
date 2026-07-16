import uuid

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.types import ASGIApp

from app.core.logging_config import request_id_var


class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        logger.debug("RequestIDMiddleware initialized")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        token = request_id_var.set(request_id)
        try:
            with logger.contextualize(request_id=request_id):
                response = await call_next(request)
                response.headers["X-Request-ID"] = request_id
                return response
        finally:
            request_id_var.reset(token)
