import tempfile
from pathlib import Path

import pytest
from app.validation.dataset.dataset_manager import DatasetManager
from app.validation.dataset.ground_truth import (
    DocumentType,
    GroundTruth,
    GroundTruthEntry,
    GroundTruthSet,
)


class TestDatasetManager:
    @pytest.fixture
    def manager(self):
        tmpdir = tempfile.mkdtemp()
        return DatasetManager(storage_dir=tmpdir)

    def _create_sample(self) -> GroundTruthSet:
        gts = GroundTruthSet(name="sample_ds", description="A sample dataset")
        doc = GroundTruth(document_id="d1", document_type=DocumentType.CBC_REPORT, document_text="CBC data")
        doc.add_entry(GroundTruthEntry(question="Q?", expected_answer="A"))
        gts.add_document(doc)
        return gts

    def test_save_and_load_dataset(self, manager):
        gts = self._create_sample()
        path = manager.save_dataset(gts)
        assert Path(path).exists()

        loaded = manager.load_dataset("sample_ds")
        assert loaded is not None
        assert loaded.name == "sample_ds"
        assert loaded.count() == 1

    def test_list_datasets(self, manager):
        assert manager.list_datasets() == []
        manager.save_dataset(self._create_sample())
        datasets = manager.list_datasets()
        assert len(datasets) == 1
        assert datasets[0]["name"] == "sample_ds"

    def test_delete_dataset(self, manager):
        manager.save_dataset(self._create_sample())
        assert manager.delete_dataset("sample_ds") is True
        assert manager.load_dataset("sample_ds") is None
        assert manager.delete_dataset("nonexistent") is False

    def test_validate_dataset(self, manager):
        manager.save_dataset(self._create_sample())
        result = manager.validate_dataset("sample_ds")
        assert result is not None
        assert result.is_valid

    def test_validate_nonexistent(self, manager):
        assert manager.validate_dataset("missing") is None

    def test_import_export(self, manager):
        gts = self._create_sample()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            import_path = f.name
        try:
            from app.validation.dataset.dataset_loader import DatasetLoader
            DatasetLoader.save_json(gts, import_path)
            imported = manager.import_from_file(import_path)
            assert imported.name == "sample_ds"
            assert manager.load_dataset("sample_ds") is not None
        finally:
            Path(import_path).unlink()

    def test_export_to_file(self, manager):
        manager.save_dataset(self._create_sample())
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            export_path = f.name
        try:
            assert manager.export_to_file("sample_ds", export_path) is True
            from app.validation.dataset.dataset_loader import DatasetLoader
            loaded = DatasetLoader.load_json(export_path)
            assert loaded.name == "sample_ds"
        finally:
            Path(export_path).unlink()

    def test_export_missing(self, manager):
        with tempfile.NamedTemporaryFile(suffix=".json") as f:
            assert manager.export_to_file("missing", f.name) is False

    def test_get_stats(self, manager):
        manager.save_dataset(self._create_sample())
        stats = manager.get_stats("sample_ds")
        assert stats is not None
        assert stats["total_documents"] == 1
        assert stats["total_entries"] == 1

    def test_get_stats_missing(self, manager):
        assert manager.get_stats("missing") is None
