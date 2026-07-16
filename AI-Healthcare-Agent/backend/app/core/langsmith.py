import os

from langsmith import Client
from loguru import logger

from app.core.config import settings


def setup_langsmith() -> Client | None:
    if not settings.LANGSMITH_API_KEY:
        logger.warning("LangSmith API key not configured — skipping LangSmith setup")
        return None

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
    os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
    os.environ["LANGSMITH_TRACING_SAMPLING_RATE"] = str(
        settings.LANGSMITH_TRACING_SAMPLING_RATE
    )

    client = Client(
        api_url="https://api.smith.langchain.com",
        api_key=settings.LANGSMITH_API_KEY,
    )
    logger.info(f"LangSmith initialized — project: {settings.LANGSMITH_PROJECT}")
    return client
