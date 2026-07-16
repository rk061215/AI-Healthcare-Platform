import logging
import logging.handlers
import json
import os
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path

from app.core.config import settings

request_id_var: ContextVar[str] = ContextVar('request_id', default='')

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get() or '-'
        return True

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
            'request_id': getattr(record, 'request_id', '-'),
        }
        if record.exc_info and record.exc_info[0]:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    request_id_filter = RequestIdFilter()

    file_handler = logging.handlers.RotatingFileHandler(
        str(log_dir / 'app.log'), maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(JsonFormatter())
    file_handler.setLevel(logging.INFO)
    file_handler.addFilter(request_id_filter)
    root_logger.addHandler(file_handler)

    error_handler = logging.handlers.RotatingFileHandler(
        str(log_dir / 'errors.log'), maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    error_handler.setFormatter(JsonFormatter())
    error_handler.setLevel(logging.ERROR)
    error_handler.addFilter(request_id_filter)
    root_logger.addHandler(error_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(request_id)-12s | %(name)s:%(funcName)s:%(lineno)d | %(message)s'
    ))
    console_handler.setLevel(logging.INFO)
    console_handler.addFilter(request_id_filter)
    root_logger.addHandler(console_handler)

    module_levels = {
        'app.core': getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        'app.api': logging.INFO,
        'app.services': logging.DEBUG if settings.DEBUG else logging.INFO,
        'app.rag': logging.DEBUG if settings.DEBUG else logging.INFO,
        'app.langgraph': logging.DEBUG if settings.DEBUG else logging.INFO,
    }
    for module, level in module_levels.items():
        logging.getLogger(module).setLevel(level)

    for noisy in ('httpx', 'httpcore', 'uvicorn.access', 'chromadb', 'PIL'):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger('app.core.logging_config').info(
        'Stdlib logging configured — file=logs/app.log, errors=logs/errors.log'
    )
