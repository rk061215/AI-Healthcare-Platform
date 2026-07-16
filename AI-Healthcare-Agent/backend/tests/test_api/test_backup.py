import os
from pathlib import Path

import pytest

from app.core.backup import BackupManager


@pytest.fixture
def backup_manager(tmp_path: Path) -> BackupManager:
    mgr = BackupManager()
    mgr.backup_dir = tmp_path / "backups"
    mgr.backup_dir.mkdir(parents=True, exist_ok=True)
    return mgr


def test_list_backups_empty(backup_manager: BackupManager):
    backups = backup_manager.list_backups()
    assert backups == []


def test_list_backups_with_files(backup_manager: BackupManager):
    f1 = backup_manager.backup_dir / "backup_20250101_000000.sql"
    f2 = backup_manager.backup_dir / "backup_20250102_000000.sql"
    f1.write_text("-- test")
    f2.write_text("-- test")
    os.utime(f1, (100, 100))
    os.utime(f2, (200, 200))

    backups = backup_manager.list_backups()
    assert len(backups) == 2
    assert backups[0]["filename"] == "backup_20250102_000000.sql"


def test_cleanup_old_backups(backup_manager: BackupManager):
    old_file = backup_manager.backup_dir / "old_backup.sql"
    old_file.write_text("-- test")
    old_time = 100  # way in the past (epoch 1 = 1970)
    os.utime(old_file, (old_time, old_time))

    new_file = backup_manager.backup_dir / "new_backup.sql"
    new_file.write_text("-- test")

    backup_manager._cleanup_old_backups()

    assert not old_file.exists()
    assert new_file.exists()


def test_restore_backup_file_not_found(backup_manager: BackupManager):
    with pytest.raises(FileNotFoundError):
        backup_manager.restore_backup("/nonexistent/backup.sql")
