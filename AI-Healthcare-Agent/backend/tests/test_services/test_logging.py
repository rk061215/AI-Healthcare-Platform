import json
import io
import sys

from app.core.logging import JSONFormatter


def test_json_formatter_basic():
    formatter = JSONFormatter()
    record = {
        "time": __import__("datetime").datetime(2026, 7, 14, 10, 30, 0, 123000),
        "level": __import__("loguru").logger.level("INFO"),
        "name": "test.logger",
        "message": "Test message",
        "extra": {},
        "exception": None,
    }
    output = formatter(record)
    parsed = json.loads(output)
    assert parsed["timestamp"] == "2026-07-14T10:30:00.123Z"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test.logger"
    assert parsed["message"] == "Test message"


def test_json_formatter_with_extra():
    formatter = JSONFormatter()
    record = {
        "time": __import__("datetime").datetime(2026, 7, 14, 10, 30, 0, 123000),
        "level": __import__("loguru").logger.level("INFO"),
        "name": "test.logger",
        "message": "Test message",
        "extra": {"request_id": "req_abc", "patient_id": "pat_123"},
        "exception": None,
    }
    output = formatter(record)
    parsed = json.loads(output)
    assert parsed["request_id"] == "req_abc"
    assert parsed["patient_id"] == "pat_123"
