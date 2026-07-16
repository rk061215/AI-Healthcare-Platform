from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from app.validation.dataset.dataset_loader import DatasetLoader
from app.validation.dataset.dataset_validator import DatasetValidator, ValidationResult
from app.validation.dataset.ground_truth import GroundTruthSet


class DatasetManager:
    def __init__(self, storage_dir: str | Path = "datasets"):
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, GroundTruthSet] = {}

    def list_datasets(self) -> list[dict[str, Any]]:
        datasets: list[dict[str, Any]] = []
        for fpath in sorted(self._storage_dir.glob("*.json")):
            try:
                gt_set = DatasetLoader.load_json(fpath)
                datasets.append({
                    "name": gt_set.name,
                    "path": str(fpath),
                    "version": gt_set.version,
                    "documents": len(gt_set.documents),
                    "entries": gt_set.count(),
                    "description": gt_set.description[:100] if gt_set.description else "",
                })
            except Exception:
                datasets.append({
                    "name": fpath.stem,
                    "path": str(fpath),
                    "version": "unknown",
                    "error": True,
                })
        return datasets

    def load_dataset(self, name: str) -> Optional[GroundTruthSet]:
        if name in self._cache:
            return self._cache[name]

        path = self._find_dataset(name)
        if path is None:
            return None
        try:
            gt_set = DatasetLoader.load_json(path)
            self._cache[name] = gt_set
            return gt_set
        except Exception:
            return None

    def save_dataset(self, gt_set: GroundTruthSet, name: Optional[str] = None) -> str:
        fname = (name or gt_set.name).replace(" ", "_").lower()
        path = self._storage_dir / f"{fname}.json"
        DatasetLoader.save_json(gt_set, path)
        self._cache[gt_set.name] = gt_set
        return str(path)

    def delete_dataset(self, name: str) -> bool:
        path = self._find_dataset(name)
        if path is None:
            return False
        path.unlink()
        self._cache.pop(name, None)
        return True

    def validate_dataset(self, name: str) -> Optional[ValidationResult]:
        gt_set = self.load_dataset(name)
        if gt_set is None:
            return None
        return DatasetValidator.validate(gt_set)

    def import_from_file(self, path: str | Path) -> GroundTruthSet:
        gt_set = DatasetLoader.load_json(path)
        self.save_dataset(gt_set)
        return gt_set

    def export_to_file(self, name: str, output_path: str | Path) -> bool:
        gt_set = self.load_dataset(name)
        if gt_set is None:
            return False
        DatasetLoader.save_json(gt_set, output_path)
        return True

    def get_stats(self, name: str) -> Optional[dict[str, Any]]:
        gt_set = self.load_dataset(name)
        if gt_set is None:
            return None
        return gt_set.stats()

    def _find_dataset(self, name: str) -> Optional[Path]:
        exact = self._storage_dir / f"{name}.json"
        if exact.exists():
            return exact
        for fpath in self._storage_dir.glob("*.json"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("name") == name:
                    return fpath
            except Exception:
                continue
        return None
