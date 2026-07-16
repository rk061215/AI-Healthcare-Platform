import sentry_sdk
from fastapi import FastAPI
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.core.config import settings


def sanitize_sentry_event(event: dict, hint: dict) -> dict | None:
    if "request" in event:
        event["request"].pop("data", None)
        event["request"].pop("cookies", None)
        if "headers" in event["request"]:
            headers = event["request"]["headers"]
            if isinstance(headers, dict):
                headers.pop("Authorization", None)
                headers.pop("authorization", None)
            elif isinstance(headers, str):
                pass

    if "user" in event:
        user = event["user"]
        safe_user = {}
        if "role" in user:
            safe_user["role"] = user["role"]
        if "id" in user:
            safe_user["id"] = user["id"]
        event["user"] = safe_user

    return event


def setup_sentry(app: FastAPI) -> None:
    if not settings.SENTRY_DSN:
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT or settings.ENVIRONMENT,
        release="0.8.0",
        traces_sample_rate=settings.OTEL_TRACE_SAMPLING_RATE,
        profiles_sample_rate=0.05,
        send_default_pii=False,
        max_breadcrumbs=50,
        attach_stacktrace=True,
        before_send=sanitize_sentry_event,
        integrations=[
            FastApiIntegration(),
        ],
    )
