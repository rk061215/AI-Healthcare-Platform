from __future__ import annotations

import json
import os
import tempfile

import pytest

from app.evaluation.dataset_loader import BenchmarkSample, DatasetLoader
from app.evaluation.exceptions import DatasetNotFoundError


class TestDatasetLoader:
    def test_list_datasets_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = DatasetLoader(dataset_path=tmpdir)
            datasets = loader.list_datasets()
            assert datasets == []

    def test_list_datasets_with_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with open(os.path.join(tmpdir, "test_dataset.json"), "w") as f:
                json.dump({"samples": []}, f)
            loader = DatasetLoader(dataset_path=tmpdir)
            datasets = loader.list_datasets()
            assert len(datasets) == 1
            assert datasets[0]["name"] == "test_dataset"

    def test_load_dataset_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = DatasetLoader(dataset_path=tmpdir)
            with pytest.raises(DatasetNotFoundError):
                loader.load_dataset("nonexistent")

    def test_load_json_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                "version": "1.0.0",
                "description": "Test dataset",
                "samples": [
                    {
                        "query": "What medication?",
                        "expected_answer": "Metformin",
                        "context_chunks": ["Patient takes metformin"],
                        "relevant_chunks": ["Patient takes metformin"],
                    }
                ],
            }
            filepath = os.path.join(tmpdir, "med_test.json")
            with open(filepath, "w") as f:
                json.dump(data, f)
            loader = DatasetLoader(dataset_path=tmpdir)
            dataset = loader.load_dataset("med_test")
            assert dataset.name == "med_test"
            assert dataset.num_samples == 1
            assert dataset.samples[0].query == "What medication?"
            assert dataset.samples[0].expected_answer == "Metformin"

    def test_load_dataset_from_category(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cat_dir = os.path.join(tmpdir, "prescriptions")
            os.makedirs(cat_dir)
            data = {
                "samples": [
                    {
                        "query": "What medication?",
                        "expected_answer": "Metformin",
                    }
                ],
            }
            with open(os.path.join(cat_dir, "rx.json"), "w") as f:
                json.dump(data, f)
            loader = DatasetLoader(dataset_path=tmpdir)
            dataset = loader.load_dataset("rx", category="prescriptions")
            assert dataset.num_samples == 1
            assert dataset.samples[0].expected_answer == "Metformin"

    def test_parse_sample_full(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                "samples": [
                    {
                        "query": "test",
                        "expected_answer": "answer",
                        "context_chunks": ["ctx1", "ctx2"],
                        "relevant_chunks": ["rel1"],
                        "citations": [{"text": "cite1"}],
                        "expected_citations": ["cite1"],
                        "expected_medications": ["med1"],
                        "expected_diagnoses": ["diag1"],
                        "expected_lab_results": [{"name": "Glucose", "value": "95"}],
                        "expected_follow_ups": ["follow up in 3 months"],
                        "retrieved_docs": ["doc1", "doc2"],
                        "relevant_docs": ["doc1"],
                        "relevance_scores": {"doc1": 0.9},
                        "metadata": {"source": "test"},
                    }
                ],
            }
            filepath = os.path.join(tmpdir, "full.json")
            with open(filepath, "w") as f:
                json.dump(data, f)
            loader = DatasetLoader(dataset_path=tmpdir)
            dataset = loader.load_dataset("full")
            sample = dataset.samples[0]
            assert sample.expected_medications == ["med1"]
            assert sample.expected_diagnoses == ["diag1"]
            assert sample.expected_lab_results == [{"name": "Glucose", "value": "95"}]
            assert sample.expected_follow_ups == ["follow up in 3 months"]
            assert sample.retrieved_docs == ["doc1", "doc2"]
            assert sample.relevance_scores == {"doc1": 0.9}

    def test_create_sample_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            samples = [
                BenchmarkSample(
                    query="What medication?",
                    expected_answer="Metformin",
                ),
            ]
            loader = DatasetLoader(dataset_path=tmpdir)
            filepath = loader.create_sample_dataset(
                category="prescriptions",
                name="test_rx",
                samples=samples,
                description="Test prescription dataset",
            )
            assert os.path.isfile(filepath)
            with open(filepath, "r") as f:
                data = json.load(f)
            assert data["description"] == "Test prescription dataset"
            assert len(data["samples"]) == 1
