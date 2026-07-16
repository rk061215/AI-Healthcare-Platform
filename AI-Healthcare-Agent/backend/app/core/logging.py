import json
import logging
import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings
from app.core.pii_filter import mask_pii_in_dict, mask_pii_in_log_message


class PIIFilter:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def __call__(self, record: dict) -> bool:
        if not self.enabled:
            return True
        if "extra" in record:
            record["extra"] = mask_pii_in_dict(record["extra"])
        record["message"] = mask_pii_in_log_message(record["message"])
        if record.get("exception"):
            record["exception"] = mask_pii_in_dict(record["exception"])
        return True


class JSONFormatter:
    def __call__(self, record: dict) -> str:
        log_entry = {
            "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.") + f"{record['time'].microsecond // 1000:03d}Z",
            "level": record["level"].name,
            "logger": record["name"],
            "message": record["message"],
        }

        if record.get("extra"):
            log_entry.update(record["extra"])

        if record.get("exception"):
            log_entry["exception"] = {
                "type": record["exception"].type.__name__ if record["exception"].type else None,
                "value": str(record["exception"].value) if record["exception"].value else None,
            }

        return json.dumps(log_entry, default=str)


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_name == "<module>":
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    is_json = settings.LOG_FORMAT == "json"
    log_level = settings.LOG_LEVEL.upper()

    logger.remove()

    pii_filter = PIIFilter(enabled=not settings.DEBUG)

    if is_json:
        formatter = JSONFormatter()
        logger.add(
            sys.stdout,
            format=formatter,
            level=log_level,
            colorize=False,
            filter=pii_filter,
        )
        logger.add(
            Path("logs") / "healthcare_{time:YYYY-MM-DD}.json",
            format=formatter,
            level=log_level,
            rotation="1 day",
            retention="30 days",
            compression="gz",
            filter=pii_filter,
        )
    else:
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        if settings.DEBUG:
            console_format += " | <magenta>{extra[request_id]}</magenta>" if False else ""

        logger.add(
            sys.stdout,
            format=console_format,
            level=log_level,
            colorize=True,
            filter=pii_filter,
        )
        logger.add(
            Path("logs") / "healthcare_{time:YYYY-MM-DD}.log",
            format=console_format,
            level=log_level,
            rotation="1 day",
            retention="30 days",
            compression="gz",
            filter=pii_filter,
        )

    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)

    for logger_name in ("uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]

    logger.info("Logging configured successfully")
