"""Production backup manager with scheduling, verification, and retention policies."""

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from loguru import logger

from app.core.config import settings


class BackupManager:
    """Manages PostgreSQL backups with rotation, verification, and scheduling support."""

    def __init__(self) -> None:
        self.backup_dir = Path(settings.BACKUP_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, label: Optional[str] = None) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        label_part = f"_{label}" if label else ""
        filename = f"backup_{timestamp}{label_part}.sql"
        backup_path = self.backup_dir / filename

        cmd = [
            "pg_dump",
            settings.DATABASE_URL,
            "-f", str(backup_path),
            "--no-owner",
            "--no-acl",
            "--verbose",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=300)
            logger.info(f"Backup created: {backup_path} ({backup_path.stat().st_size} bytes)")
        except subprocess.TimeoutExpired:
            backup_path.unlink(missing_ok=True)
            raise RuntimeError("Database backup timed out after 300 seconds")
        except subprocess.CalledProcessError as e:
            backup_path.unlink(missing_ok=True)
            logger.error(f"Backup failed: {e.stderr}")
            raise RuntimeError(f"Database backup failed: {e.stderr}") from e
        except FileNotFoundError as e:
            backup_path.unlink(missing_ok=True)
            logger.error("pg_dump not found. Is PostgreSQL installed?")
            raise RuntimeError("pg_dump not found. Is PostgreSQL installed?") from e

        self._cleanup_old_backups()
        return backup_path

    def restore_backup(self, backup_path: str | Path) -> None:
        backup_path = Path(backup_path)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        if backup_path.stat().st_size == 0:
            raise ValueError(f"Backup file is empty: {backup_path}")

        cmd = [
            "psql",
            settings.DATABASE_URL,
            "-f", str(backup_path),
            "--echo-errors",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=600)
            logger.info(f"Backup restored from: {backup_path}")
        except subprocess.TimeoutExpired:
            raise RuntimeError("Database restore timed out after 600 seconds")
        except subprocess.CalledProcessError as e:
            logger.error(f"Restore failed: {e.stderr[:2000]}")
            raise RuntimeError(f"Database restore failed: {e.stderr[:2000]}") from e
        except FileNotFoundError as e:
            logger.error("psql not found. Is PostgreSQL installed?")
            raise RuntimeError("psql not found. Is PostgreSQL installed?") from e

    def verify_backup(self, backup_path: str | Path) -> dict:
        backup_path = Path(backup_path)
        if not backup_path.exists():
            return {"valid": False, "error": "File not found"}
        if backup_path.stat().st_size == 0:
            return {"valid": False, "error": "Empty file"}

        first_lines = backup_path.read_text(encoding="utf-8", errors="replace")[:500]

        is_valid = False
        format_type = "unknown"

        if first_lines.strip().startswith("--"):
            if "PostgreSQL" in first_lines or "pg_dump" in first_lines:
                is_valid = True
                format_type = "plain SQL"
        elif first_lines.startswith("PGDMP"):
            is_valid = True
            format_type = "custom (compressed)"

        return {
            "valid": is_valid,
            "format": format_type,
            "size_bytes": backup_path.stat().st_size,
            "created_at": datetime.fromtimestamp(backup_path.stat().st_mtime, tz=timezone.utc).isoformat(),
        }

    def list_backups(self) -> list[dict]:
        backups = sorted(self.backup_dir.glob("*.sql"), key=os.path.getmtime, reverse=True)
        return [
            {
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "size_display": _format_bytes(f.stat().st_size),
                "created_at": datetime.fromtimestamp(
                    f.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
                "path": str(f.absolute()),
            }
            for f in backups
        ]

    def _cleanup_old_backups(self) -> None:
        backups = sorted(self.backup_dir.glob("*.sql"), key=os.path.getmtime)
        retention_seconds = settings.BACKUP_RETENTION_DAYS * 86400
        now = datetime.now(timezone.utc).timestamp()

        removed = 0
        for backup in backups:
            if now - backup.stat().st_mtime > retention_seconds:
                backup.unlink()
                removed += 1
                logger.info(f"Removed expired backup: {backup}")

        if removed:
            logger.info(f"Cleanup complete: removed {removed} expired backup(s)")


def _format_bytes(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
