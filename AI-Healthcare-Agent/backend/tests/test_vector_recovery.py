"""Tests for the Vector Recovery Manager.

Tests cover: fresh startup, missing ChromaDB, deleted collection,
version mismatch, partial rebuild, incremental rebuild, recovery
interruption, recovery retry, corrupt index, health endpoint, and
automatic startup recovery on ephemeral filesystem (Phase U.8).
"""

from datetime import datetime, timezone
from itertools import cycle
from unittest.mock import MagicMock, call, patch

import pytest

from app.database.enums import IndexStatus
from app.models.report import Report
from app.models.vector_index_state import VectorIndexState
from app.vector_recovery.config import RecoveryConfig, get_embedding_model_key
from app.vector_recovery.exceptions import RebuildFailedError
from app.vector_recovery.health import VectorHealth, get_rebuild_progress, set_rebuild_progress
from app.vector_recovery.recovery_manager import RecoveryManager


@pytest.fixture
def mock_services():
    vector_service = MagicMock()
    embedding_service = MagicMock()
    document_pipeline = MagicMock()

    vector_service.health_check.return_value = {
        "vector_store": {"status": "ok", "document_count": 5},
        "embedding_service": {"status": "ok"},
    }
    vector_service.index_chunks.return_value = ["chunk_1", "chunk_2"]
    vector_service.store.initialize.return_value = None
    vector_service.close.return_value = None

    embedding_service.health_check.return_value = {"status": "ok"}
    embedding_service.provider = MagicMock()
    embedding_service.provider.provider_name.return_value = "gemini"
    embedding_service.provider.model_name.return_value = "text-embedding-004"

    document_pipeline.process.return_value = [
        MagicMock(
            text="test chunk text",
            chunk_id="test_chunk_1",
            metadata=MagicMock(
                chunk_version="1.0.0",
                schema_version="1.0.0",
                embedding_version="",
                document_type="lab_report",
                patient_id="p1",
                report_id="r1",
                section="results",
                page=1,
                chunk_index=0,
                source="ocr",
                language="en",
                provider="tesseract",
            ),
        ),
    ]

    return vector_service, embedding_service, document_pipeline


def _setup_health(mock_db, total=0, indexed=0, pending=0, failed=0):
    """Configure mock_db for check_health()'s 6 scalar calls.
    
    Uses repeatable (cycle) side_effect so check_health() can be called
    multiple times (e.g. run_startup_recovery calls it twice).
    
    Direct .scalar() calls (queries 1 and 6): return_value = total
    Filter .scalar() calls (queries 2-5): cycle([indexed, pending, failed, None])
    """
    mock_db.query.return_value.scalar.return_value = total
    mock_db.query.return_value.filter.return_value.scalar.side_effect = cycle([
        indexed, pending, failed, None,
    ])


def _mgr(vs, es, dp, **kwargs):
    config = kwargs.pop("config", None) or RecoveryConfig(enabled=False)
    return RecoveryManager(
        vector_service=vs,
        embedding_service=es,
        document_pipeline=dp,
        config=config,
    )


def _report(id="r1", pid="p1", text="test text", status="completed"):
    r = MagicMock(spec=Report)
    r.id = id
    r.patient_id = pid
    r.ocr_text = text
    r.ocr_provider = "tesseract"
    r.status = status
    return r


_CHUNK_METADATA_KWARGS = dict(
    chunk_version="1.0.0",
    schema_version="1.0.0",
    embedding_version="",
    document_type="lab_report",
    patient_id="p1",
    report_id="r1",
    section="results",
    page=1,
    chunk_index=0,
    source="ocr",
    language="en",
    provider="tesseract",
)


@pytest.fixture
def mock_db(mocker):
    db = MagicMock()
    mocker.patch("app.vector_recovery.recovery_manager.SessionLocal", return_value=db)
    return db


class TestVectorHealth:
    def test_healthy_defaults(self):
        vh = VectorHealth()
        assert vh.status == "healthy"
        assert vh.collection_exists is False
        assert vh.indexed_reports == 0
        assert vh.actual_document_count == 0

    def test_to_dict_includes_actual_document_count(self):
        vh = VectorHealth(
            status="degraded",
            collection_exists=True,
            indexed_reports=5,
            actual_document_count=2,
            pending_rebuild_count=2,
        )
        d = vh.to_dict()
        assert d["status"] == "degraded"
        assert d["indexed_reports"] == 5
        assert d["actual_document_count"] == 2
        assert d["pending_rebuild_count"] == 2

    def test_to_dict_defaults(self):
        vh = VectorHealth()
        d = vh.to_dict()
        assert d["status"] == "healthy"
        assert d["actual_document_count"] == 0

    def test_to_dict_with_datetime(self):
        now = datetime.now(timezone.utc)
        vh = VectorHealth(last_rebuild_at=now)
        d = vh.to_dict()
        assert d["last_rebuild_at"] == now.isoformat()

    def test_to_dict_with_none_datetime(self):
        vh = VectorHealth()
        d = vh.to_dict()
        assert d["last_rebuild_at"] is None

    def test_rebuild_progress_global(self):
        set_rebuild_progress(in_progress=True, total=10, completed=3, failed=1)
        p = get_rebuild_progress()
        assert p["in_progress"] is True
        assert p["total"] == 10
        assert p["completed"] == 3

    def test_rebuild_progress_roundtrip(self):
        set_rebuild_progress(in_progress=True, total=5, completed=2, failed=1)
        assert get_rebuild_progress()["completed"] == 2
        set_rebuild_progress(in_progress=False)
        assert get_rebuild_progress()["in_progress"] is False


class TestRecoveryConfig:
    def test_default_config(self):
        cfg = RecoveryConfig()
        assert cfg.enabled is True
        assert cfg.batch_size == 5
        assert cfg.batch_delay_seconds == 0.5

    def test_embedding_model_key(self):
        with patch("app.vector_recovery.config.settings") as mock_settings:
            mock_settings.EMBEDDING_PROVIDER = "gemini"
            mock_settings.EMBEDDING_MODEL = "text-embedding-004"
            key = get_embedding_model_key()
            assert key == "gemini:text-embedding-004"


class TestRecoveryManager:
    # ── check_health() tests ─────────────────────────────────────────

    def test_healthy(self, mock_services, mock_db):
        vs, es, dp = mock_services
        vs.health_check.return_value = {
            "vector_store": {"status": "ok", "document_count": 10},
            "embedding_service": {"status": "ok"},
        }
        mgr = _mgr(vs, es, dp)
        _setup_health(mock_db, total=10, indexed=10)

        health = mgr.check_health()
        assert health.status == "healthy"
        assert health.total_reports == 10
        assert health.indexed_reports == 10
        assert health.actual_document_count == 10

    def test_healthy_zero_reports(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        _setup_health(mock_db, total=0, indexed=0)

        health = mgr.check_health()
        assert health.status == "healthy"
        assert health.total_reports == 0
        assert health.actual_document_count == 5

    def test_degraded_when_collection_missing(self, mock_services, mock_db):
        vs, es, dp = mock_services
        vs.health_check.return_value = {
            "vector_store": {"status": "error", "error": "Not initialized"},
        }
        mgr = _mgr(vs, es, dp)
        _setup_health(mock_db, total=10, indexed=0)

        health = mgr.check_health()
        assert health.status == "degraded"
        assert health.collection_exists is False

    def test_degraded_when_pending(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        _setup_health(mock_db, total=10, indexed=8, pending=2)

        health = mgr.check_health()
        assert health.status == "degraded"
        assert health.pending_rebuild_count == 2

    def test_degraded_when_failed(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        _setup_health(mock_db, total=10, indexed=6, pending=0, failed=2)

        health = mgr.check_health()
        assert health.status == "degraded"
        assert health.failed_rebuild_count == 2

    def test_degraded_when_indexed_mismatch(self, mock_services, mock_db):
        vs, es, dp = mock_services
        vs.health_check.return_value = {
            "vector_store": {"status": "ok", "document_count": 2},
        }
        mgr = _mgr(vs, es, dp)
        _setup_health(mock_db, total=5, indexed=5)

        health = mgr.check_health()
        assert health.status == "degraded"
        assert health.indexed_reports == 5
        assert health.actual_document_count == 2

    def test_rebuilding_status(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        _setup_health(mock_db, total=5, indexed=5)
        set_rebuild_progress(in_progress=True, total=5, completed=2)

        health = mgr.check_health()
        assert health.status == "rebuilding"
        assert health.rebuild_in_progress is True

    def test_healthy_with_matching_counts(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        set_rebuild_progress()
        _setup_health(mock_db, total=5, indexed=5)

        health = mgr.check_health()
        assert health.status == "healthy"
        assert health.indexed_reports == 5
        assert health.actual_document_count == 5

    def test_check_error_on_exception(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        mock_db.query.return_value.filter.return_value.scalar.side_effect = RuntimeError("DB connection lost")

        health = mgr.check_health()
        assert health.status == "error"

    def test_healthy_with_rebuild_in_progress_false(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        _setup_health(mock_db, total=3, indexed=3)
        set_rebuild_progress(in_progress=False)

        health = mgr.check_health()
        assert health.status == "healthy"
        assert health.rebuild_in_progress is False

    # ── needs_rebuild() tests ────────────────────────────────────────

    def test_needs_rebuild_true_when_degraded(self, mock_services, mock_db):
        vs, es, dp = mock_services
        vs.health_check.return_value = {"vector_store": {"status": "error"}}
        mgr = _mgr(vs, es, dp)
        _setup_health(mock_db, total=5, indexed=0)

        assert mgr.needs_rebuild() is True

    def test_needs_rebuild_false_when_healthy(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        _setup_health(mock_db, total=5, indexed=5)

        assert mgr.needs_rebuild() is False

    # ── rebuild_all() tests ──────────────────────────────────────────

    def test_rebuild_all_no_work(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.side_effect = [[], []]

        count = mgr.rebuild_all()
        assert count == 0

    def test_rebuild_all_with_work(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp, config=RecoveryConfig(batch_size=2, batch_delay_seconds=0))

        report = _report()

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [report]
        mock_db.query.return_value.filter.return_value.all.side_effect = [[], []]

        count = mgr.rebuild_all()
        assert count == 1

    # ── rebuild_report() tests ───────────────────────────────────────

    def test_rebuild_report_success(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)

        report = _report()
        mock_db.query.return_value.filter.return_value.first.return_value = report

        success = mgr.rebuild_report("00000000-0000-0000-0000-000000000001")
        assert success is True

    def test_rebuild_report_not_found(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        success = mgr.rebuild_report("r1")
        assert success is False

    def test_rebuild_report_fails_on_no_ocr(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)

        report = _report(text=None)
        mock_db.query.return_value.filter.return_value.first.return_value = report

        success = mgr.rebuild_report("r1")
        assert success is False

    # ── verify_index() tests ─────────────────────────────────────────

    def test_verify_index_counts(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        mock_db.query.return_value.scalar.side_effect = [10, 5]
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [8, 0, 1, 1, 0]

        result = mgr.verify_index()
        assert result["total_reports"] == 10
        assert result["indexed"] == 8
        assert result["stale"] == 1

    def test_verify_index_mismatch(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        mock_db.query.return_value.scalar.side_effect = [8, 5]
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [5, 2, 0, 0, 0]

        result = mgr.verify_index()
        assert result["healthy"] is False

    # ── cleanup_orphans() tests ──────────────────────────────────────

    def test_cleanup_orphans(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)

        orphan = MagicMock(spec=VectorIndexState)
        orphan.report_id = "orphan_id"
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [orphan]

        count = mgr.cleanup_orphans()
        assert count == 1

    # ── _determine_work() tests ──────────────────────────────────────

    def test_determine_work_unindexed(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)

        report = _report()
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [report]
        mock_db.query.return_value.filter.return_value.all.side_effect = [[], []]

        work = mgr._determine_work(mock_db)
        assert len(work) == 1
        assert work[0].id == report.id

    def test_determine_work_unindexed_only(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)

        report = _report()
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [report]
        mock_db.query.return_value.filter.return_value.all.side_effect = [[], []]

        work = mgr._determine_work(mock_db)
        assert len(work) == 1  # only unindexed report

    # ── run_startup_recovery() tests ─────────────────────────────────

    def test_startup_recovery_disabled(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp, config=RecoveryConfig(enabled=False))
        _setup_health(mock_db, total=5, indexed=0)

        health = mgr.run_startup_recovery()
        assert health.status == "healthy"

    def test_startup_recovery_healthy(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp, config=RecoveryConfig(rebuild_on_startup=False))
        _setup_health(mock_db, total=5, indexed=5)

        health = mgr.run_startup_recovery()
        assert health.status == "healthy"

    def test_startup_recovery_initializes_missing_collection(self, mock_services, mock_db):
        vs, es, dp = mock_services
        vs.health_check.return_value = {
            "vector_store": {"status": "error", "error": "not found"},
        }
        mgr = _mgr(vs, es, dp, config=RecoveryConfig(rebuild_on_startup=False))
        _setup_health(mock_db, total=5, indexed=0)

        health = mgr.run_startup_recovery()
        vs.store.initialize.assert_called_once()
        assert health.status == "degraded"

    def test_startup_recovery_marks_stale_on_mismatch(self, mock_services, mock_db):
        vs, es, dp = mock_services
        vs.health_check.return_value = {
            "vector_store": {"status": "ok", "document_count": 0},
        }
        mgr = _mgr(vs, es, dp, config=RecoveryConfig(rebuild_on_startup=False))
        _setup_health(mock_db, total=5, indexed=5)

        with patch.object(mgr, "_mark_all_indexed_as_stale") as mock_mark:
            health = mgr.run_startup_recovery()
            mock_mark.assert_called_once()

        assert health.status == "degraded"

    def test_startup_recovery_no_mark_when_matching(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp, config=RecoveryConfig(rebuild_on_startup=False))
        _setup_health(mock_db, total=5, indexed=5)

        with patch.object(mgr, "_mark_all_indexed_as_stale") as mock_mark:
            health = mgr.run_startup_recovery()
            mock_mark.assert_not_called()

        assert health.status == "healthy"

    def test_startup_recovery_performs_rebuild(self, mock_services, mock_db):
        vs, es, dp = mock_services
        vs.health_check.return_value = {
            "vector_store": {"status": "ok", "document_count": 0},
        }
        mgr = _mgr(vs, es, dp, config=RecoveryConfig(rebuild_on_startup=True, batch_delay_seconds=0))
        _setup_health(mock_db, total=5, indexed=5)

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.side_effect = [[], []]

        with patch.object(mgr, "_mark_all_indexed_as_stale") as mock_mark:
            health = mgr.run_startup_recovery()
            mock_mark.assert_called_once()

    # ── _mark_all_indexed_as_stale() tests ───────────────────────────

    def test_mark_all_indexed_as_stale(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        mock_db.query.return_value.filter.return_value.update.return_value = 3

        count = mgr._mark_all_indexed_as_stale()
        assert count == 3
        mock_db.commit.assert_called_once()

    def test_mark_all_indexed_as_stale_zero(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        mock_db.query.return_value.filter.return_value.update.return_value = 0

        count = mgr._mark_all_indexed_as_stale()
        assert count == 0

    def test_mark_all_indexed_as_stale_rollback_on_error(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)
        mock_db.query.return_value.filter.return_value.update.side_effect = RuntimeError("update failed")

        count = mgr._mark_all_indexed_as_stale()
        assert count == 0
        mock_db.rollback.assert_called_once()

    # ── rebuild_progress_tracking tests ──────────────────────────────

    def test_rebuild_progress_tracking(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp, config=RecoveryConfig(batch_size=2, batch_delay_seconds=0))

        report = _report()
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [report]
        mock_db.query.return_value.filter.return_value.all.side_effect = [[], []]

        mgr.rebuild_all()
        progress = get_rebuild_progress()
        assert progress["in_progress"] is False
        assert progress["completed"] == 1

    # ── show_status() tests ─────────────────────────────────────────

    def test_show_status_structure(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = _mgr(vs, es, dp)

        mock_db.query.return_value.scalar.return_value = 0
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [
            0, 0, 0, 0, 0, 0, 0,  # verify_index: 7 values
            0, 0, 0, None, None,  # check_health: 5 filter values
        ]

        status = mgr.show_status()
        assert "health" in status
        assert "index_verification" in status
        assert "config" in status


class TestExceptions:
    def test_rebuild_failed_error(self):
        with pytest.raises(RebuildFailedError) as exc_info:
            raise RebuildFailedError("test failure")
        assert "test failure" in str(exc_info.value)


class TestIndexStatus:
    def test_enum_values(self):
        assert IndexStatus.PENDING.value == "pending"
        assert IndexStatus.INDEXED.value == "indexed"
        assert IndexStatus.STALE.value == "stale"
        assert IndexStatus.FAILED.value == "failed"
        assert IndexStatus.REBUILDING.value == "rebuilding"
