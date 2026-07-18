import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.logging import JSONFormatter, setup_logging
from app.core.config import Settings


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


# ── Cloud-native logging tests ─────────────────────────────


def test_resolved_log_dir_default_development():
    """Development with no LOG_DIR and no container signals → ./logs"""
    settings = Settings(ENVIRONMENT="development", LOG_DIR="")
    assert settings.resolved_log_dir == "./logs"


def test_resolved_log_dir_production_no_container():
    """Production without LOG_DIR and no container signals → ./logs"""
    settings = Settings(ENVIRONMENT="production", LOG_DIR="")
    with patch.dict(os.environ, {}, clear=True):
        assert settings.resolved_log_dir == ""


def test_resolved_log_dir_custom():
    """Explicit LOG_DIR overrides everything"""
    settings = Settings(LOG_DIR="/custom/logs")
    assert settings.resolved_log_dir == "/custom/logs"


def test_resolved_log_dir_empty_in_container():
    """Container env var disables file logging"""
    with patch.dict(os.environ, {"RENDER": "true"}, clear=True):
        settings = Settings(ENVIRONMENT="development", LOG_DIR="")
        assert settings.resolved_log_dir == ""


def test_setup_logging_stdout_always():
    """setup_logging always adds stdout — never fails"""
    settings = Settings(LOG_DIR="", DEBUG=False)
    with patch("app.core.logging.settings", settings):
        setup_logging()  # should not raise


def test_setup_logging_file_works(tmp_path):
    """File logging writes when LOG_DIR is writable"""
    log_dir = str(tmp_path / "logs")
    settings = Settings(LOG_DIR=log_dir, DEBUG=False)
    with patch("app.core.logging.settings", settings):
        setup_logging()
        assert (tmp_path / "logs").exists()


def test_setup_logging_unwritable_dir(tmp_path):
    """PermissionError on LOG_DIR does not crash startup"""
    unwritable = str(tmp_path / "nope")
    Path(unwritable).mkdir(parents=True, exist_ok=True)

    with patch("app.core.logging.settings", Settings(LOG_DIR=unwritable, DEBUG=False)):
        setup_logging()


def test_resolved_log_dir_k8s_detection():
    """KUBERNETES_SERVICE_HOST detected as container"""
    with patch.dict(os.environ, {"KUBERNETES_SERVICE_HOST": "10.0.0.1"}, clear=True):
        settings = Settings(ENVIRONMENT="development", LOG_DIR="")
        assert settings.resolved_log_dir == ""


def test_resolved_log_dir_dockerenv(tmp_path):
    "/.dockerenv file detected as container"
    with patch("os.path.exists", return_value=True):
        settings = Settings(ENVIRONMENT="development", LOG_DIR="")
        assert settings.resolved_log_dir == ""


def test_setup_logging_stdlib_stdout_only(tmp_path):
    """stdlib logging works with stdout only when dir unwritable"""
    from app.core.logging_config import setup_logging as stdlib_setup

    unwritable = str(tmp_path / "restricted")
    Path(unwritable).mkdir(parents=True, exist_ok=True)
    import stat
    old_mode = os.stat(unwritable).st_mode
    os.chmod(unwritable, stat.S_IRUSR | stat.S_IXUSR)  # remove write
    try:
        with patch("app.core.logging_config.settings", Settings(LOG_DIR=unwritable, DEBUG=False)):
            stdlib_setup()
    finally:
        os.chmod(unwritable, old_mode)
