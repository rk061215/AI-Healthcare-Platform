import json
import tempfile
from pathlib import Path

import pytest
from app.validation.dataset.dataset_loader import DatasetLoader
from app.validation.dataset.ground_truth import DocumentType, GroundTruthSet


class TestDatasetLoader:
    SAMPLE_DATA = {
        "name": "test_dataset",
        "description": "Test dataset",
        "version": "1.0.0",
        "format_version": "1.0.0",
        "metadata": {},
        "documents": [
            {
                "document_id": "doc_001",
                "document_type": "cbc_report",
                "document_text": "CBC results text",
                "structured_extraction": {"wbc": "8.5"},
                "metadata": {},
                "version": "1.0.0",
                "entries": [
                    {
                        "question": "What is WBC?",
                        "expected_answer": "WBC is 8.5",
                        "expected_citations": ["doc_001:wbc"],
                        "expected_medical_concepts": ["wbc"],
                        "difficulty": "easy",
                        "category": "lab_result",
                        "ground_truth_document": "",
                        "ground_truth_extraction": {},
                        "expected_confidence": 0.95,
                        "notes": "",
                    }
                ],
            }
        ],
    }

    def test_load_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.SAMPLE_DATA, f)
            fpath = f.name
        try:
            gt_set = DatasetLoader.load_json(fpath)
            assert isinstance(gt_set, GroundTruthSet)
            assert gt_set.name == "test_dataset"
            assert gt_set.count() == 1
            assert gt_set.documents[0].document_type == DocumentType.CBC_REPORT
        finally:
            Path(fpath).unlink()

    def test_save_and_reload(self):
        gt_set = DatasetLoader._from_dict(self.SAMPLE_DATA)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            fpath = f.name
        try:
            DatasetLoader.save_json(gt_set, fpath)
            loaded = DatasetLoader.load_json(fpath)
            assert loaded.name == gt_set.name
            assert loaded.count() == gt_set.count()
        finally:
            Path(fpath).unlink()

    def test_load_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            DatasetLoader.load_json("/nonexistent/path.json")

    def test_load_jsonl(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            json.dump(self.SAMPLE_DATA, f)
            f.write("\n")
            json.dump(self.SAMPLE_DATA, f)
            fpath = f.name
        try:
            sets = DatasetLoader.load_jsonl(fpath)
            assert len(sets) == 2
            assert all(s.name == "test_dataset" for s in sets)
        finally:
            Path(fpath).unlink()

    def test_load_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = Path(tmpdir) / "test.json"
            with open(fpath, "w") as f:
                json.dump(self.SAMPLE_DATA, f)
            sets = DatasetLoader.load_directory(tmpdir)
            assert len(sets) == 1
            assert sets[0].name == "test_dataset"

    def test_roundtrip_preserves_entries(self):
        gt_set = DatasetLoader._from_dict(self.SAMPLE_DATA)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            fpath = f.name
        try:
            DatasetLoader.save_json(gt_set, fpath)
            loaded = DatasetLoader.load_json(fpath)
            entry = loaded.documents[0].entries[0]
            assert entry.question == "What is WBC?"
            assert entry.expected_answer == "WBC is 8.5"
            assert entry.expected_citations == ["doc_001:wbc"]
            assert entry.expected_confidence == 0.95
        finally:
            Path(fpath).unlink()

    def test_from_dict_with_invalid_doc_type(self):
        data = dict(self.SAMPLE_DATA)
        data["documents"][0]["document_type"] = "invalid_type"
        gt_set = DatasetLoader._from_dict(data)
        assert gt_set.documents[0].document_type == DocumentType.CLINICAL_NOTES
