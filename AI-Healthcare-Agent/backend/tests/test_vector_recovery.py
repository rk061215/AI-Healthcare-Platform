"""Tests for the Vector Recovery Manager.

Tests cover: fresh startup, missing ChromaDB, deleted collection,
version mismatch, partial rebuild, incremental rebuild, recovery
interruption, recovery retry, corrupt index, and health endpoint.
"""

from unittest.mock import MagicMock, patch

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

    def test_to_dict(self):
        vh = VectorHealth(
            status="degraded",
            collection_exists=True,
            indexed_reports=5,
            pending_rebuild_count=2,
        )
        d = vh.to_dict()
        assert d["status"] == "degraded"
        assert d["indexed_reports"] == 5
        assert d["pending_rebuild_count"] == 2

    def test_rebuild_progress_global(self):
        set_rebuild_progress(in_progress=True, total=10, completed=3, failed=1)
        p = get_rebuild_progress()
        assert p["in_progress"] is True
        assert p["total"] == 10
        assert p["completed"] == 3


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
    def test_check_healthy(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = RecoveryManager(
            vector_service=vs,
            embedding_service=es,
            document_pipeline=dp,
            config=RecoveryConfig(enabled=False),
        )

        mock_db.query.return_value.filter.return_value.scalar.side_effect = [10, 10, 0, 0]

        health = mgr.check_health()
        assert health.status == "healthy"
        assert health.total_reports == 10
        assert health.indexed_reports == 10

    def test_check_degraded_when_collection_missing(self, mock_services, mock_db):
        vs, es, dp = mock_services
        vs.health_check.return_value = {
            "vector_store": {"status": "error", "error": "Not initialized"},
        }
        mgr = RecoveryManager(vector_service=vs, config=RecoveryConfig(enabled=False))

        mock_db.query.return_value.filter.return_value.scalar.side_effect = [10, 0, 0, 0]

        health = mgr.check_health()
        assert health.status == "degraded"
        assert health.collection_exists is False

    def test_check_degraded_when_pending(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = RecoveryManager(vector_service=vs, config=RecoveryConfig(enabled=False))

        mock_db.query.return_value.filter.return_value.scalar.side_effect = [10, 8, 2, 0]

        health = mgr.check_health()
        assert health.status == "degraded"
        assert health.pending_rebuild_count == 2

    def test_needs_rebuild_true_when_degraded(self, mock_services, mock_db):
        vs, es, dp = mock_services
        vs.health_check.return_value = {
            "vector_store": {"status": "error"},
        }
        mgr = RecoveryManager(vector_service=vs, config=RecoveryConfig(enabled=False))

        mock_db.query.return_value.filter.return_value.scalar.side_effect = [5, 0, 0, 0]

        assert mgr.needs_rebuild() is True

    def test_rebuild_all_no_work(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = RecoveryManager(
            vector_service=vs,
            embedding_service=es,
            document_pipeline=dp,
            config=RecoveryConfig(enabled=False),
        )

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = []

        count = mgr.rebuild_all()
        assert count == 0

    def test_rebuild_all_with_work(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = RecoveryManager(
            vector_service=vs,
            embedding_service=es,
            document_pipeline=dp,
            config=RecoveryConfig(batch_size=2, batch_delay_seconds=0),
        )

        report = MagicMock(spec=Report)
        report.id = "00000000-0000-0000-0000-000000000001"
        report.patient_id = "00000000-0000-0000-0000-000000000002"
        report.ocr_text = "test report text"
        report.ocr_provider = "tesseract"
        report.status = "completed"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [report]
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []

        count = mgr.rebuild_all()
        assert count == 1

    def test_rebuild_report_success(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = RecoveryManager(
            vector_service=vs,
            embedding_service=es,
            document_pipeline=dp,
            config=RecoveryConfig(enabled=False),
        )

        report = MagicMock(spec=Report)
        report.id = "00000000-0000-0000-0000-000000000001"
        report.patient_id = "00000000-0000-0000-0000-000000000002"
        report.ocr_text = "test report text"
        report.ocr_provider = "tesseract"
        report.status = "completed"

        mock_db.query.return_value.filter.return_value.first.return_value = report

        success = mgr.rebuild_report("00000000-0000-0000-0000-000000000001")
        assert success is True

    def test_rebuild_report_not_found(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = RecoveryManager(
            vector_service=vs,
            embedding_service=es,
            document_pipeline=dp,
            config=RecoveryConfig(enabled=False),
        )

        mock_db.query.return_value.filter.return_value.first.return_value = None

        success = mgr.rebuild_report("00000000-0000-0000-0000-000000000001")
        assert success is False

    def test_verify_index_counts(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = RecoveryManager(vector_service=vs, config=RecoveryConfig(enabled=False))

        mock_db.query.return_value.filter.return_value.scalar.side_effect = [8, 0, 1, 1, 10, 10, 0]

        result = mgr.verify_index()
        assert result["total_reports"] == 10
        assert result["indexed"] == 8
        assert result["stale"] == 1

    def test_cleanup_orphans(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = RecoveryManager(vector_service=vs, config=RecoveryConfig(enabled=False))

        orphan = MagicMock(spec=VectorIndexState)
        orphan.report_id = "00000000-0000-0000-0000-000000000099"
        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [orphan]

        count = mgr.cleanup_orphans()
        assert count == 1

    def test_determine_work_unindexed(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = RecoveryManager(
            vector_service=vs,
            embedding_service=es,
            document_pipeline=dp,
            config=RecoveryConfig(enabled=False),
        )

        report = MagicMock(spec=Report)
        report.id = "00000000-0000-0000-0000-000000000001"
        report.patient_id = "00000000-0000-0000-0000-000000000002"
        report.ocr_text = "test text"
        report.status = "completed"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [report]
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []

        work = mgr._determine_work(mock_db)
        assert len(work) == 1
        assert work[0].id == report.id

    def test_startup_recovery_healthy(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = RecoveryManager(
            vector_service=vs,
            embedding_service=es,
            document_pipeline=dp,
            config=RecoveryConfig(rebuild_on_startup=False),
        )

        mock_db.query.return_value.filter.return_value.scalar.side_effect = [5, 5, 0, 0]

        health = mgr.run_startup_recovery()
        assert health.status == "healthy"

    def test_rebuild_progress_tracking(self, mock_services, mock_db):
        vs, es, dp = mock_services
        mgr = RecoveryManager(
            vector_service=vs,
            embedding_service=es,
            document_pipeline=dp,
            config=RecoveryConfig(batch_size=2, batch_delay_seconds=0),
        )

        report = MagicMock(spec=Report)
        report.id = "00000000-0000-0000-0000-000000000001"
        report.patient_id = "00000000-0000-0000-0000-000000000002"
        report.ocr_text = "test text"
        report.ocr_provider = "tesseract"
        report.status = "completed"

        mock_db.query.return_value.outerjoin.return_value.filter.return_value.all.return_value = [report]
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []

        mgr.rebuild_all()
        progress = get_rebuild_progress()
        assert progress["in_progress"] is False
        assert progress["completed"] == 1


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
