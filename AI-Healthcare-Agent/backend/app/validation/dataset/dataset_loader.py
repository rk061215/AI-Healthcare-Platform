from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from app.validation.dataset.ground_truth import (
    DifficultyLevel,
    DocumentType,
    GroundTruth,
    GroundTruthEntry,
    GroundTruthSet,
    QuestionCategory,
)


class DatasetLoader:
    FORMAT_VERSION = "1.0.0"

    @staticmethod
    def load_json(path: str | Path) -> GroundTruthSet:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Dataset not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return DatasetLoader._from_dict(data)

    @staticmethod
    def load_jsonl(path: str | Path) -> list[GroundTruthSet]:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Dataset not found: {p}")
        sets: list[GroundTruthSet] = []
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    sets.append(DatasetLoader._from_dict(data))
        return sets

    @staticmethod
    def load_directory(path: str | Path) -> list[GroundTruthSet]:
        p = Path(path)
        if not p.is_dir():
            raise NotADirectoryError(f"Not a directory: {p}")
        sets: list[GroundTruthSet] = []
        for fpath in sorted(p.glob("*")):
            if fpath.suffix in (".json", ".jsonl"):
                if fpath.suffix == ".json":
                    sets.append(DatasetLoader.load_json(fpath))
                else:
                    sets.extend(DatasetLoader.load_jsonl(fpath))
        return sets

    @staticmethod
    def _from_dict(data: dict[str, Any]) -> GroundTruthSet:
        gt_set = GroundTruthSet(
            name=data.get("name", "unnamed"),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            metadata=data.get("metadata", {}),
        )
        for doc_data in data.get("documents", []):
            doc_type_str = doc_data.get("document_type", "clinical_notes")
            try:
                doc_type = DocumentType(doc_type_str)
            except ValueError:
                doc_type = DocumentType.CLINICAL_NOTES
            doc = GroundTruth(
                document_id=doc_data.get("document_id", ""),
                document_type=doc_type,
                document_text=doc_data.get("document_text", ""),
                structured_extraction=doc_data.get("structured_extraction", {}),
                metadata=doc_data.get("metadata", {}),
                version=doc_data.get("version", "1.0.0"),
            )
            for entry_data in doc_data.get("entries", []):
                diff_str = entry_data.get("difficulty", "medium")
                try:
                    difficulty = DifficultyLevel(diff_str)
                except ValueError:
                    difficulty = DifficultyLevel.MEDIUM
                cat_str = entry_data.get("category", "diagnosis")
                try:
                    category = QuestionCategory(cat_str)
                except ValueError:
                    category = QuestionCategory.DIAGNOSIS
                entry = GroundTruthEntry(
                    question=entry_data.get("question", ""),
                    expected_answer=entry_data.get("expected_answer", ""),
                    expected_citations=entry_data.get("expected_citations", []),
                    expected_medical_concepts=entry_data.get("expected_medical_concepts", []),
                    difficulty=difficulty,
                    category=category,
                    ground_truth_document=entry_data.get("ground_truth_document", ""),
                    ground_truth_extraction=entry_data.get("ground_truth_extraction", {}),
                    expected_confidence=entry_data.get("expected_confidence", 0.9),
                    notes=entry_data.get("notes", ""),
                )
                doc.add_entry(entry)
            gt_set.add_document(doc)
        return gt_set

    @staticmethod
    def save_json(gt_set: GroundTruthSet, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = DatasetLoader._to_dict(gt_set)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    @staticmethod
    def save_jsonl(sets: list[GroundTruthSet], path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            for gt_set in sets:
                data = DatasetLoader._to_dict(gt_set)
                f.write(json.dumps(data, default=str) + "\n")

    @staticmethod
    def _to_dict(gt_set: GroundTruthSet) -> dict[str, Any]:
        return {
            "name": gt_set.name,
            "description": gt_set.description,
            "version": gt_set.version,
            "format_version": DatasetLoader.FORMAT_VERSION,
            "metadata": gt_set.metadata,
            "documents": [
                {
                    "document_id": doc.document_id,
                    "document_type": doc.document_type.value,
                    "document_text": doc.document_text,
                    "structured_extraction": doc.structured_extraction,
                    "metadata": doc.metadata,
                    "version": doc.version,
                    "entries": [
                        {
                            "question": e.question,
                            "expected_answer": e.expected_answer,
                            "expected_citations": e.expected_citations,
                            "expected_medical_concepts": e.expected_medical_concepts,
                            "difficulty": e.difficulty.value,
                            "category": e.category.value,
                            "ground_truth_document": e.ground_truth_document,
                            "ground_truth_extraction": e.ground_truth_extraction,
                            "expected_confidence": e.expected_confidence,
                            "notes": e.notes,
                        }
                        for e in doc.entries
                    ],
                }
                for doc in gt_set.documents
            ],
        }
