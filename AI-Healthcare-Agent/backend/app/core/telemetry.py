from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from app.core.config import settings


def setup_opentelemetry(app) -> None:
    resource = Resource.create({
        "service.name": settings.OTEL_SERVICE_NAME,
        "service.version": "0.8.0",
        "deployment.environment": settings.ENVIRONMENT,
    })

    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    try:
        if settings.OTEL_EXPORTER_OTLP_ENDPOINT and settings.ENVIRONMENT != "test":
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    except Exception:
        pass

    trace.set_tracer_provider(provider)


def get_tracer(name: str = "ai-healthcare") -> trace.Tracer:
    return trace.get_tracer(name)
