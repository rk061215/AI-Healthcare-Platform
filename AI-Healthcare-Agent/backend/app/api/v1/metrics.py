"""Prometheus metrics endpoint."""

from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

from app.middleware.metrics import (
    http_request_duration_seconds,
    http_requests_in_flight,
    http_requests_total,
    http_request_size_bytes,
    http_response_size_bytes,
)

router = APIRouter()


@router.get("/metrics", include_in_schema=False)
def metrics_endpoint():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
