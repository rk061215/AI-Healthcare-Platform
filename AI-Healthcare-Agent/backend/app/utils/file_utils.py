import hashlib
import uuid
from pathlib import Path

from app.core.config import settings


def get_file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def save_upload_file(content: bytes, extension: str) -> Path:
    file_id = str(uuid.uuid4())
    file_path = settings.upload_path / f"{file_id}{extension}"
    file_path.write_bytes(content)
    return file_path
