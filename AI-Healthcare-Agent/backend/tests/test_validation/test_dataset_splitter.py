import pytest
from app.validation.dataset.dataset_splitter import DatasetSplitter
from app.validation.dataset.ground_truth import (
    DocumentType,
    DifficultyLevel,
    GroundTruth,
    GroundTruthEntry,
    GroundTruthSet,
    QuestionCategory,
)


class TestDatasetSplitter:
    def _make_set(self, num_docs: int = 3, entries_per_doc: int = 5) -> GroundTruthSet:
        gts = GroundTruthSet(name="split_test")
        for i in range(num_docs):
            doc = GroundTruth(
                document_id=f"d{i}",
                document_type=DocumentType.CLINICAL_NOTES,
                document_text=f"Document {i}",
            )
            for j in range(entries_per_doc):
                doc.add_entry(GroundTruthEntry(
                    question=f"Q{i}_{j}?", expected_answer=f"A{i}_{j}",
                ))
            gts.add_document(doc)
        return gts

    def test_split_by_ratio(self):
        gts = self._make_set(num_docs=1, entries_per_doc=100)
        splits = DatasetSplitter.split(gts, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)
        assert "train" in splits
        assert "val" in splits
        assert "test" in splits
        total = splits["train"].count() + splits["val"].count() + splits["test"].count()
        assert total == gts.count()

    def test_split_by_document(self):
        gts = self._make_set(num_docs=10, entries_per_doc=3)
        splits = DatasetSplitter.split_by_document(gts, train_ratio=0.6, val_ratio=0.2)
        total_docs = (
            len(splits["train"].documents)
            + len(splits["val"].documents)
            + len(splits["test"].documents)
        )
        assert total_docs == len(gts.documents)

    def test_split_invalid_ratios(self):
        gts = self._make_set()
        with pytest.raises(ValueError, match="must sum to 1.0"):
            DatasetSplitter.split(gts, train_ratio=0.5, val_ratio=0.3, test_ratio=0.3)

    def test_split_seed_determinism(self):
        gts = self._make_set(num_docs=1, entries_per_doc=50)
        s1 = DatasetSplitter.split(gts, seed=42)
        s2 = DatasetSplitter.split(gts, seed=42)
        assert s1["train"].count() == s2["train"].count()
        assert s1["val"].count() == s2["val"].count()

    def test_split_different_seed(self):
        gts = self._make_set(num_docs=1, entries_per_doc=50)
        s1 = DatasetSplitter.split(gts, seed=42)
        s2 = DatasetSplitter.split(gts, seed=99)
        assert s1["train"].count() == s2["train"].count()

    def test_small_dataset(self):
        gts = self._make_set(num_docs=1, entries_per_doc=2)
        splits = DatasetSplitter.split(gts, train_ratio=0.5, val_ratio=0.25, test_ratio=0.25)
        total = sum(s.count() for s in splits.values())
        assert total == gts.count()
