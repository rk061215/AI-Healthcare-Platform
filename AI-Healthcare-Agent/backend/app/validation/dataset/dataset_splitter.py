from __future__ import annotations

import random
from typing import Any

from app.validation.dataset.ground_truth import GroundTruthSet


class DatasetSplitter:
    @staticmethod
    def split(
        gt_set: GroundTruthSet,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        shuffle: bool = True,
        seed: int = 42,
    ) -> dict[str, GroundTruthSet]:
        ratios = train_ratio + val_ratio + test_ratio
        if abs(ratios - 1.0) > 0.001:
            raise ValueError(f"Ratios must sum to 1.0, got {ratios}")

        entries = list(gt_set.all_entries())
        if shuffle:
            rng = random.Random(seed)
            rng.shuffle(entries)

        n = len(entries)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)

        train_entries = entries[:train_end]
        val_entries = entries[train_end:val_end]
        test_entries = entries[val_end:]

        train_set = GroundTruthSet(
            name=f"{gt_set.name}_train",
            description=f"Training split of {gt_set.name}",
            version=gt_set.version,
            metadata={"split": "train", "source": gt_set.name, **gt_set.metadata},
        )
        val_set = GroundTruthSet(
            name=f"{gt_set.name}_val",
            description=f"Validation split of {gt_set.name}",
            version=gt_set.version,
            metadata={"split": "val", "source": gt_set.name, **gt_set.metadata},
        )
        test_set = GroundTruthSet(
            name=f"{gt_set.name}_test",
            description=f"Test split of {gt_set.name}",
            version=gt_set.version,
            metadata={"split": "test", "source": gt_set.name, **gt_set.metadata},
        )

        for doc in gt_set.documents:
            doc_entries = [e for e in train_entries if e in doc.entries]
            if doc_entries:
                train_doc_copy = DatasetSplitter._copy_doc(doc, doc_entries)
                train_set.add_document(train_doc_copy)

            doc_entries = [e for e in val_entries if e in doc.entries]
            if doc_entries:
                val_doc_copy = DatasetSplitter._copy_doc(doc, doc_entries)
                val_set.add_document(val_doc_copy)

            doc_entries = [e for e in test_entries if e in doc.entries]
            if doc_entries:
                test_doc_copy = DatasetSplitter._copy_doc(doc, doc_entries)
                test_set.add_document(test_doc_copy)

        return {"train": train_set, "val": val_set, "test": test_set}

    @staticmethod
    def _copy_doc(doc: Any, entries: list) -> Any:
        from copy import deepcopy
        from app.validation.dataset.ground_truth import GroundTruth

        new_doc = GroundTruth(
            document_id=doc.document_id,
            document_type=doc.document_type,
            document_text=doc.document_text,
            structured_extraction=deepcopy(doc.structured_extraction),
            metadata=deepcopy(doc.metadata),
            version=doc.version,
        )
        for e in entries:
            new_doc.add_entry(e)
        return new_doc

    @staticmethod
    def split_by_document(
        gt_set: GroundTruthSet,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        seed: int = 42,
    ) -> dict[str, GroundTruthSet]:
        docs = list(gt_set.documents)
        rng = random.Random(seed)
        rng.shuffle(docs)

        n = len(docs)
        train_end = max(1, int(n * train_ratio))
        val_end = train_end + max(1, int(n * val_ratio))

        train_docs = docs[:train_end]
        val_docs = docs[train_end:val_end]
        test_docs = docs[val_end:]

        train_set = GroundTruthSet(name=f"{gt_set.name}_train", metadata={"split": "train"})
        val_set = GroundTruthSet(name=f"{gt_set.name}_val", metadata={"split": "val"})
        test_set = GroundTruthSet(name=f"{gt_set.name}_test", metadata={"split": "test"})

        for d in train_docs:
            train_set.add_document(d)
        for d in val_docs:
            val_set.add_document(d)
        for d in test_docs:
            test_set.add_document(d)

        return {"train": train_set, "val": val_set, "test": test_set}
