from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Optional

from app.evaluation.exceptions import DatasetError, DatasetNotFoundError


@dataclass
class BenchmarkSample:
    query: str
    expected_answer: str
    context_chunks: list[str] = field(default_factory=list)
    relevant_chunks: list[str] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    expected_citations: list[str] = field(default_factory=list)
    expected_medications: list[str] = field(default_factory=list)
    expected_diagnoses: list[str] = field(default_factory=list)
    expected_lab_results: list[dict[str, str]] = field(default_factory=list)
    expected_follow_ups: list[str] = field(default_factory=list)
    retrieved_docs: list[str] = field(default_factory=list)
    relevant_docs: list[str] = field(default_factory=list)
    relevance_scores: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkDataset:
    name: str
    category: str
    samples: list[BenchmarkSample] = field(default_factory=list)
    version: str = "1.0.0"
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def num_samples(self) -> int:
        return len(self.samples)


class DatasetLoader:
    SUPPORTED_FORMATS: tuple[str, ...] = (".json", ".jsonl")

    def __init__(self, dataset_path: str = "datasets") -> None:
        self._dataset_path = dataset_path

    def load_dataset(
        self,
        name: str,
        category: Optional[str] = None,
    ) -> BenchmarkDataset:
        search_paths: list[str] = []
        if category:
            search_paths.append(os.path.join(self._dataset_path, category, f"{name}.json"))
            search_paths.append(os.path.join(self._dataset_path, category, f"{name}.jsonl"))
        search_paths.append(os.path.join(self._dataset_path, f"{name}.json"))
        search_paths.append(os.path.join(self._dataset_path, f"{name}.jsonl"))
        search_paths.append(os.path.join(self._dataset_path, category or "", f"{name}", "dataset.json"))
        search_paths.append(os.path.join(self._dataset_path, category or "", f"{name}", "dataset.jsonl"))
        for path in search_paths:
            if os.path.isfile(path):
                return self._load_file(path, name, category or "")
        raise DatasetNotFoundError(
            f"Dataset '{name}' not found in '{self._dataset_path}' "
            f"(searched {len(search_paths)} locations)"
        )

    def list_datasets(self, category: Optional[str] = None) -> list[dict[str, str]]:
        search_dir = os.path.join(self._dataset_path, category) if category else self._dataset_path
        if not os.path.isdir(search_dir):
            return []
        datasets: list[dict[str, str]] = []
        for fname in os.listdir(search_dir):
            if fname.endswith(".json") or fname.endswith(".jsonl"):
                name = os.path.splitext(fname)[0]
                datasets.append({
                    "name": name,
                    "path": os.path.join(search_dir, fname),
                    "format": os.path.splitext(fname)[1],
                })
            full_path = os.path.join(search_dir, fname)
            if os.path.isdir(full_path):
                dataset_file = os.path.join(full_path, "dataset.json")
                if os.path.isfile(dataset_file):
                    datasets.append({
                        "name": fname,
                        "path": dataset_file,
                        "format": ".json",
                    })
        return datasets

    def _load_file(self, path: str, name: str, category: str) -> BenchmarkDataset:
        _, ext = os.path.splitext(path)
        if ext == ".json":
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self._parse_json_dataset(data, name, category)
        elif ext == ".jsonl":
            samples: list[BenchmarkSample] = []
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        samples.append(self._parse_sample(data))
            return BenchmarkDataset(
                name=name,
                category=category,
                samples=samples,
                version="1.0.0",
            )
        raise DatasetError(f"Unsupported file format: {ext}")

    def _parse_json_dataset(self, data: dict[str, Any], name: str, category: str) -> BenchmarkDataset:
        raw_samples = data.get("samples", data.get("data", []))
        samples = [self._parse_sample(s) for s in raw_samples]
        return BenchmarkDataset(
            name=name,
            category=category,
            samples=samples,
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            metadata=data.get("metadata", {}),
        )

    def _parse_sample(self, data: dict[str, Any]) -> BenchmarkSample:
        return BenchmarkSample(
            query=data.get("query", ""),
            expected_answer=data.get("expected_answer", data.get("answer", "")),
            context_chunks=data.get("context_chunks", data.get("context", [])),
            relevant_chunks=data.get("relevant_chunks", data.get("relevant", [])),
            citations=data.get("citations", []),
            expected_citations=data.get("expected_citations", []),
            expected_medications=data.get("expected_medications", []),
            expected_diagnoses=data.get("expected_diagnoses", []),
            expected_lab_results=data.get("expected_lab_results", []),
            expected_follow_ups=data.get("expected_follow_ups", []),
            retrieved_docs=data.get("retrieved_docs", []),
            relevant_docs=data.get("relevant_docs", []),
            relevance_scores=data.get("relevance_scores", {}),
            metadata=data.get("metadata", {}),
        )

    def create_sample_dataset(
        self,
        category: str,
        name: str,
        samples: list[BenchmarkSample],
        description: str = "",
    ) -> str:
        category_dir = os.path.join(self._dataset_path, category)
        os.makedirs(category_dir, exist_ok=True)
        filepath = os.path.join(category_dir, f"{name}.json")
        data = {
            "version": "1.0.0",
            "description": description,
            "category": category,
            "samples": [
                {
                    "query": s.query,
                    "expected_answer": s.expected_answer,
                    "context_chunks": s.context_chunks,
                    "relevant_chunks": s.relevant_chunks,
                    "citations": s.citations,
                    "expected_citations": s.expected_citations,
                    "expected_medications": s.expected_medications,
                    "expected_diagnoses": s.expected_diagnoses,
                    "expected_lab_results": s.expected_lab_results,
                    "expected_follow_ups": s.expected_follow_ups,
                    "retrieved_docs": s.retrieved_docs,
                    "relevant_docs": s.relevant_docs,
                    "relevance_scores": s.relevance_scores,
                    "metadata": s.metadata,
                }
                for s in samples
            ],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return filepath
