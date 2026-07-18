from __future__ import annotations

import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from loguru import logger
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.enums import IndexStatus
from app.database.session import SessionLocal
from app.document_pipeline.document import ProcessedDocument
from app.document_pipeline.pipeline import DocumentPipeline
from app.embeddings.embedding_service import EmbeddingService
from app.models.report import Report
from app.models.vector_index_state import VectorIndexState
from app.vector_recovery.base_recovery_manager import BaseRecoveryManager
from app.vector_recovery.config import RecoveryConfig, get_embedding_model_key
from app.vector_recovery.exceptions import (
    CollectionMissingError,
    RebuildFailedError,
    RebuildInterruptedError,
)
from app.vector_recovery.health import (
    VectorHealth,
    get_rebuild_progress,
    set_rebuild_progress,
)
from app.vector_store.vector_service import VectorService


class RecoveryManager(BaseRecoveryManager):
    def __init__(
        self,
        vector_service: Optional[VectorService] = None,
        embedding_service: Optional[EmbeddingService] = None,
        document_pipeline: Optional[DocumentPipeline] = None,
        config: Optional[RecoveryConfig] = None,
        db_factory=None,
    ):
        self._vector_service = vector_service or VectorService()
        self._embedding_service = embedding_service or EmbeddingService()
        self._pipeline = document_pipeline or DocumentPipeline()
        self._config = config or RecoveryConfig()
        self._db_factory = db_factory or SessionLocal
        self._embedding_model_key = ""

    def _get_db(self) -> Session:
        return self._db_factory()

    def _current_model_key(self) -> str:
        if not self._embedding_model_key:
            self._embedding_model_key = get_embedding_model_key(self._embedding_service)
        return self._embedding_model_key

    def check_health(self) -> VectorHealth:
        health = VectorHealth(embedding_model_version=self._current_model_key())
        db = self._get_db()
        try:
            try:
                vs_health = self._vector_service.health_check()
                store = vs_health.get("vector_store", {})
                health.collection_exists = store.get("status") == "ok"
                health.actual_document_count = store.get("document_count", 0)
            except Exception:
                health.collection_exists = False
                health.actual_document_count = 0

            total = db.query(func.count(Report.id)).scalar() or 0
            indexed = (
                db.query(func.count(VectorIndexState.id))
                .filter(VectorIndexState.index_status == IndexStatus.INDEXED.value)
                .scalar()
                or 0
            )
            pending = (
                db.query(func.count(VectorIndexState.id))
                .filter(VectorIndexState.index_status.in_([
                    IndexStatus.PENDING.value,
                    IndexStatus.STALE.value,
                    IndexStatus.FAILED.value,
                ]))
                .scalar()
                or 0
            )
            failed_count = (
                db.query(func.count(VectorIndexState.id))
                .filter(VectorIndexState.index_status == IndexStatus.FAILED.value)
                .scalar()
                or 0
            )

            last_indexed = (
                db.query(func.max(VectorIndexState.last_indexed_at))
                .filter(VectorIndexState.index_status == IndexStatus.INDEXED.value)
                .scalar()
            )
            last_verified = (
                db.query(func.max(VectorIndexState.last_verified_at)).scalar()
            )

            health.total_reports = total
            health.indexed_reports = indexed
            health.pending_rebuild_count = pending
            health.failed_rebuild_count = failed_count
            health.last_rebuild_at = last_indexed
            health.last_verified_at = last_verified

            progress = get_rebuild_progress()
            health.rebuild_in_progress = progress.get("in_progress", False)

            if not health.collection_exists and total > 0:
                health.status = "degraded"
            elif pending > 0:
                health.status = "degraded"
            elif failed_count > 0:
                health.status = "degraded"
            elif (
                indexed > health.actual_document_count
                and total > 0
            ):
                health.status = "degraded"
            else:
                health.status = "healthy"

            if health.rebuild_in_progress:
                health.status = "rebuilding"

            health.details = {
                "rebuild_progress": progress,
                "collection_status": store.get("status") if health.collection_exists else "missing",
                "actual_document_count": health.actual_document_count,
                "expected_report_count": indexed,
            }
        except Exception as exc:
            health.status = "error"
            health.details = {"error": str(exc)}
        finally:
            db.close()
        return health

    def needs_rebuild(self) -> bool:
        health = self.check_health()
        return health.status != "healthy" or not health.collection_exists

    def rebuild_all(self) -> int:
        db = self._get_db()
        total = 0
        completed_count = 0
        failed_count = 0
        try:
            reports_needing_index = self._determine_work(db)
            if not reports_needing_index:
                logger.info("Vector index is up-to-date — no reports need rebuilding")
                return 0

            total = len(reports_needing_index)
            model_key = self._current_model_key()
            set_rebuild_progress(
                in_progress=True,
                total=total,
                completed=0,
                failed=0,
                started_at=datetime.now(timezone.utc),
            )

            logger.info(f"Vector rebuild: {total} reports to index (model={model_key})")
            completed_count = 0
            failed_count = 0

            for i, report_row in enumerate(reports_needing_index):
                try:
                    self._index_single_report(db, report_row, model_key)
                    completed_count += 1
                    set_rebuild_progress(
                        in_progress=True,
                        total=total,
                        completed=completed_count,
                        failed=failed_count,
                    )
                    logger.info(
                        f"Rebuild progress: [{i+1}/{total}] report {report_row.id} indexed"
                    )
                except Exception as exc:
                    failed_count += 1
                    self._mark_report_failed(db, report_row.id, str(exc))
                    logger.error(f"Rebuild failed for report {report_row.id}: {exc}")
                    set_rebuild_progress(
                        in_progress=True,
                        total=total,
                        completed=completed_count,
                        failed=failed_count,
                    )

                if i < total - 1 and self._config.batch_delay_seconds > 0:
                    time.sleep(self._config.batch_delay_seconds)

            logger.info(
                f"Vector rebuild complete: {completed_count} succeeded, "
                f"{failed_count} failed out of {total}"
            )
            return completed_count
        except Exception as exc:
            logger.error(f"Vector rebuild failed: {exc}")
            raise RebuildFailedError(str(exc)) from exc
        finally:
            set_rebuild_progress(in_progress=False, total=total, completed=completed_count, failed=failed_count)
            db.close()

    def rebuild_report(self, report_id: str) -> bool:
        db = self._get_db()
        try:
            report_uuid = uuid.UUID(report_id) if isinstance(report_id, str) else report_id
            report = db.query(Report).filter(Report.id == report_uuid).first()
            if not report:
                logger.warning(f"Report {report_id} not found — cannot index")
                return False
            model_key = self._current_model_key()
            self._index_single_report(db, report, model_key)
            logger.info(f"Report {report_id} indexed successfully")
            return True
        except Exception as exc:
            logger.error(f"Failed to index report {report_id}: {exc}")
            return False
        finally:
            db.close()

    def verify_index(self) -> dict:
        db = self._get_db()
        try:
            indexed_count = (
                db.query(func.count(VectorIndexState.id))
                .filter(VectorIndexState.index_status == IndexStatus.INDEXED.value)
                .scalar()
                or 0
            )
            pending_count = (
                db.query(func.count(VectorIndexState.id))
                .filter(VectorIndexState.index_status == IndexStatus.PENDING.value)
                .scalar()
                or 0
            )
            stale_count = (
                db.query(func.count(VectorIndexState.id))
                .filter(VectorIndexState.index_status == IndexStatus.STALE.value)
                .scalar()
                or 0
            )
            failed_count = (
                db.query(func.count(VectorIndexState.id))
                .filter(VectorIndexState.index_status == IndexStatus.FAILED.value)
                .scalar()
                or 0
            )
            total_reports = db.query(func.count(Report.id)).scalar() or 0
            total_state_entries = db.query(func.count(VectorIndexState.id)).scalar() or 0

            version_mismatch = 0
            if total_state_entries > 0:
                current_model = self._current_model_key()
                mismatches = (
                    db.query(func.count(VectorIndexState.id))
                    .filter(
                        VectorIndexState.embedding_model_version != current_model,
                        VectorIndexState.index_status == IndexStatus.INDEXED.value,
                    )
                    .scalar()
                    or 0
                )
                version_mismatch = mismatches

            try:
                vs_health = self._vector_service.health_check()
                collection_ok = vs_health.get("vector_store", {}).get("status") == "ok"
            except Exception:
                collection_ok = False

            return {
                "collection_exists": collection_ok,
                "total_reports": total_reports,
                "state_entries": total_state_entries,
                "indexed": indexed_count,
                "pending": pending_count,
                "stale": stale_count,
                "failed": failed_count,
                "version_mismatch": version_mismatch,
                "current_embedding_model": self._current_model_key(),
                "healthy": collection_ok and indexed_count == total_reports and version_mismatch == 0,
            }
        finally:
            db.close()

    def cleanup_orphans(self) -> int:
        db = self._get_db()
        try:
            orphaned = (
                db.query(VectorIndexState)
                .outerjoin(Report, VectorIndexState.report_id == Report.id)
                .filter(Report.id.is_(None))
                .all()
            )
            count = len(orphaned)
            for entry in orphaned:
                db.delete(entry)
            db.commit()
            if count > 0:
                logger.info(f"Cleaned up {count} orphaned vector index state entries")
            return count
        except Exception as exc:
            db.rollback()
            logger.error(f"Failed to clean up orphans: {exc}")
            raise
        finally:
            db.close()

    def show_status(self) -> dict:
        verify = self.verify_index()
        health = self.check_health()
        return {
            "health": health.to_dict(),
            "index_verification": verify,
            "config": {
                "enabled": self._config.enabled,
                "batch_size": self._config.batch_size,
                "batch_delay_seconds": self._config.batch_delay_seconds,
                "rebuild_on_startup": self._config.rebuild_on_startup,
            },
        }

    def run_startup_recovery(self) -> VectorHealth:
        if not self._config.enabled:
            logger.info("Vector recovery disabled by configuration")
            return self.check_health()

        health = self.check_health()
        if health.status == "healthy":
            logger.info("Vector index is healthy — no recovery needed")
            return health

        logger.info(
            f"Vector index status: {health.status} "
            f"(collection={health.collection_exists}, "
            f"pending={health.pending_rebuild_count}, "
            f"failed={health.failed_rebuild_count}, "
            f"actual_docs={health.actual_document_count}, "
            f"indexed={health.indexed_reports})"
        )

        if not health.collection_exists:
            logger.warning("Vector collection missing — initializing new collection")
            try:
                self._vector_service.store.initialize()
            except Exception as exc:
                logger.error(f"Failed to initialize vector collection: {exc}")

        # Detect empty store with stale vector_index_state entries (e.g. after
        # redeploy on ephemeral filesystem). Reset INDEXED → STALE so that
        # _determine_work() picks them up for rebuild.
        if (
            health.indexed_reports > health.actual_document_count
            and health.indexed_reports > 0
        ):
            logger.warning(
                f"Vector store content mismatch: "
                f"indexed_reports={health.indexed_reports}, "
                f"actual_document_count={health.actual_document_count}. "
                "Marking indexed entries as stale for rebuild."
            )
            self._mark_all_indexed_as_stale()

        if self._config.rebuild_on_startup:
            logger.info("Starting automatic vector rebuild")
            try:
                rebuilt = self.rebuild_all()
                health_after = self.check_health()
                logger.info(
                    f"Startup recovery complete: {rebuilt} reports indexed, "
                    f"status={health_after.status}"
                )
                return health_after
            except Exception as exc:
                logger.error(f"Startup recovery failed: {exc}")
                return self.check_health()

        return self.check_health()

    def _mark_all_indexed_as_stale(self) -> int:
        db = self._get_db()
        try:
            count = (
                db.query(VectorIndexState)
                .filter(VectorIndexState.index_status == IndexStatus.INDEXED.value)
                .update(
                    {VectorIndexState.index_status: IndexStatus.STALE.value},
                    synchronize_session=False,
                )
            )
            db.commit()
            if count > 0:
                logger.info(f"Marked {count} indexed entries as stale for rebuild")
            return count
        except Exception as exc:
            db.rollback()
            logger.error(f"Failed to mark indexed entries as stale: {exc}")
            return 0
        finally:
            db.close()

    def _determine_work(self, db: Session) -> list:
        current_model = self._current_model_key()

        unindexed = (
            db.query(Report)
            .outerjoin(
                VectorIndexState,
                Report.id == VectorIndexState.report_id,
            )
            .filter(VectorIndexState.id.is_(None))
            .filter(Report.ocr_text.isnot(None))
            .filter(Report.status == "completed")
            .all()
        )

        stale_entries = (
            db.query(VectorIndexState)
            .filter(
                VectorIndexState.index_status.in_([
                    IndexStatus.PENDING.value,
                    IndexStatus.STALE.value,
                    IndexStatus.FAILED.value,
                ])
            )
            .all()
        )
        stale_report_ids = {e.report_id for e in stale_entries}
        stale_reports = (
            db.query(Report)
            .filter(Report.id.in_(stale_report_ids))
            .filter(Report.ocr_text.isnot(None))
            .all()
        ) if stale_report_ids else []

        version_mismatch_entries = (
            db.query(VectorIndexState)
            .filter(
                VectorIndexState.embedding_model_version != current_model,
                VectorIndexState.index_status == IndexStatus.INDEXED.value,
            )
            .all()
        )
        version_mismatch_ids = {e.report_id for e in version_mismatch_entries}
        version_mismatch_reports = (
            db.query(Report)
            .filter(Report.id.in_(version_mismatch_ids))
            .filter(Report.ocr_text.isnot(None))
            .all()
        ) if version_mismatch_ids else []

        seen = set()
        result = []
        for report in unindexed + stale_reports + version_mismatch_reports:
            if report.id not in seen:
                result.append(report)
                seen.add(report.id)

        logger.info(
            f"Determined work: {len(unindexed)} unindexed, "
            f"{len(stale_reports)} stale, "
            f"{len(version_mismatch_reports)} version mismatch, "
            f"{len(result)} total unique reports to rebuild"
        )
        return result

    def _index_single_report(
        self,
        db: Session,
        report: Report,
        model_key: str,
    ) -> None:
        report_id_str = str(report.id)
        patient_id_str = str(report.patient_id)

        if not report.ocr_text:
            raise ValueError(f"Report {report.id} has no OCR text")

        chunks = self._pipeline.process(
            raw_text=report.ocr_text,
            patient_id=patient_id_str,
            report_id=report_id_str,
            source="ocr",
            language="en",
            provider=report.ocr_provider or "unknown",
        )

        if not chunks:
            raise ValueError(f"Report {report.id} produced zero chunks")

        indexed_ids = self._vector_service.index_chunks(chunks)

        chunk_text = " ".join(c.text for c in chunks)
        checksum = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()

        existing = (
            db.query(VectorIndexState)
            .filter(VectorIndexState.report_id == report.id)
            .first()
        )

        if existing:
            existing.embedding_model_version = model_key
            existing.chunk_version = chunks[0].metadata.chunk_version
            existing.schema_version = chunks[0].metadata.schema_version
            existing.chunk_count = len(chunks)
            existing.index_status = IndexStatus.INDEXED.value
            existing.index_checksum = checksum
            existing.error_message = None
            existing.last_indexed_at = datetime.now(timezone.utc)
        else:
            entry = VectorIndexState(
                report_id=report.id,
                patient_id=report.patient_id,
                embedding_model_version=model_key,
                chunk_version=chunks[0].metadata.chunk_version,
                schema_version=chunks[0].metadata.schema_version,
                chunk_count=len(chunks),
                index_status=IndexStatus.INDEXED.value,
                index_checksum=checksum,
                last_indexed_at=datetime.now(timezone.utc),
            )
            db.add(entry)

        db.commit()

    def _mark_report_failed(
        self,
        db: Session,
        report_id: uuid.UUID,
        error: str,
    ) -> None:
        existing = (
            db.query(VectorIndexState)
            .filter(VectorIndexState.report_id == report_id)
            .first()
        )
        if existing:
            existing.index_status = IndexStatus.FAILED.value
            existing.error_message = error[:500]
        else:
            entry = VectorIndexState(
                report_id=report_id,
                patient_id=uuid.UUID(int=0),
                embedding_model_version=self._current_model_key(),
                index_status=IndexStatus.FAILED.value,
                error_message=error[:500],
            )
            db.add(entry)
        db.commit()
