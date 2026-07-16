"""Generate a sample evaluation report to demonstrate the evaluation framework."""

from __future__ import annotations

import json
import os
import time

from app.evaluation import (
    BenchmarkRunner,
    EvaluationConfig,
    BenchmarkDataset,
    BenchmarkSample,
)


def main() -> None:
    config = EvaluationConfig(
        benchmark_name="sample_evaluation",
        benchmark_version="1.0.0",
        k_values=(1, 3, 5),
        num_runs=1,
        report_include_raw_data=True,
        output_path="evaluation_reports",
    )

    samples = [
        BenchmarkSample(
            query="What medications is the patient taking?",
            expected_answer="The patient is taking metformin 500mg twice daily and lisinopril 10mg once daily.",
            context_chunks=[
                "Medications: Metformin 500mg - Take 1 tablet twice daily",
                "Lisinopril 10mg - Take 1 tablet once daily for blood pressure",
                "Patient has type 2 diabetes and hypertension",
            ],
            relevant_chunks=[
                "Medications: Metformin 500mg - Take 1 tablet twice daily",
                "Lisinopril 10mg - Take 1 tablet once daily for blood pressure",
            ],
            citations=[
                {"text": "Metformin 500mg - Take 1 tablet twice daily", "source": "medication_list"},
                {"text": "Lisinopril 10mg - Take 1 tablet once daily", "source": "medication_list"},
            ],
            expected_citations=[
                "Metformin 500mg - Take 1 tablet twice daily",
                "Lisinopril 10mg - Take 1 tablet once daily",
            ],
            expected_medications=["metformin", "lisinopril"],
            expected_diagnoses=["type 2 diabetes", "hypertension"],
            expected_lab_results=[
                {"name": "HbA1c", "value": "7.2"},
                {"name": "Blood Pressure", "value": "135/85"},
            ],
            expected_follow_ups=["Follow up in 3 months", "Monitor blood pressure weekly"],
            retrieved_docs=["doc_med_1", "doc_med_2", "doc_lab_1", "doc_diag_1"],
            relevant_docs=["doc_med_1", "doc_med_2"],
            relevance_scores={
                "doc_med_1": 0.95,
                "doc_med_2": 0.88,
                "doc_lab_1": 0.45,
                "doc_diag_1": 0.30,
            },
            metadata={"category": "medication", "difficulty": "easy"},
        ),
        BenchmarkSample(
            query="What was the patient's latest HbA1c result?",
            expected_answer="The patient's latest HbA1c is 7.2%, which is above the target of 7.0%.",
            context_chunks=[
                "HbA1c: 7.2% (Date: 2026-06-15)",
                "Target HbA1c: <7.0%",
                "Glucose (fasting): 126 mg/dL",
            ],
            relevant_chunks=[
                "HbA1c: 7.2% (Date: 2026-06-15)",
                "Target HbA1c: <7.0%",
            ],
            citations=[
                {"text": "HbA1c: 7.2%", "source": "lab_report"},
            ],
            expected_citations=["HbA1c: 7.2%"],
            expected_lab_results=[
                {"name": "HbA1c", "value": "7.2"},
            ],
            retrieved_docs=["doc_lab_1", "doc_lab_2", "doc_med_1"],
            relevant_docs=["doc_lab_1"],
            relevance_scores={
                "doc_lab_1": 0.92,
                "doc_lab_2": 0.60,
                "doc_med_1": 0.10,
            },
            metadata={"category": "lab_result", "difficulty": "medium"},
        ),
        BenchmarkSample(
            query="Are there any concerns about the patient's heart condition?",
            expected_answer="I don't have enough information about the patient's heart condition.",
            context_chunks=[
                "Patient has hypertension - diagnosed 2024",
                "Lisinopril 10mg once daily for blood pressure management",
            ],
            relevant_chunks=[
                "Patient has hypertension - diagnosed 2024",
            ],
            citations=[],
            expected_citations=[],
            expected_diagnoses=["hypertension"],
            retrieved_docs=["doc_diag_1", "doc_med_2"],
            relevant_docs=["doc_diag_1"],
            relevance_scores={
                "doc_diag_1": 0.75,
                "doc_med_2": 0.55,
            },
            metadata={"category": "diagnosis", "difficulty": "hard"},
        ),
    ]

    dataset = BenchmarkDataset(
        name="sample_medical_qa",
        category="general",
        samples=samples,
        version="1.0.0",
        description="Sample medical QA benchmark dataset for testing the evaluation framework",
    )

    runner = BenchmarkRunner(config=config)

    print("Running benchmark...")
    start = time.time()
    results = runner.run_benchmark(dataset=dataset)
    elapsed = time.time() - start
    print(f"Benchmark completed in {elapsed:.2f}s")

    print("\n" + "=" * 70)
    print("SAMPLE EVALUATION REPORT")
    print("=" * 70)
    print(f"Benchmark: {results.benchmark_name} v{results.benchmark_version}")
    print(f"Dataset: {results.dataset_name} ({results.num_samples} samples)")
    print(f"Duration: {results.total_duration_seconds:.2f}s")
    print()

    for category, cat_results in [
        ("RETRIEVAL METRICS", results.retrieval_results),
        ("RAG METRICS", results.rag_results),
        ("HALLUCINATION METRICS", results.hallucination_results),
        ("CITATION METRICS", results.citation_results),
    ]:
        if not cat_results:
            continue
        print(f"--- {category} ---")
        for metric in cat_results:
            score_str = f"{metric.score * 100:.1f}%" if metric.score <= 1.0 else f"{metric.score:.2f}"
            print(f"  {metric.metric_name:40s} {score_str:>8s}")
        print()

    report_path = runner.generate_report(results)
    print(f"Report saved to: {report_path}")

    with open(report_path, "r") as f:
        report_data = json.load(f)
    print(f"\nReport JSON keys: {list(report_data.keys())}")
    print(f"Metrics categories: {list(report_data['metrics'].keys())}")
    for cat, metrics in report_data["metrics"].items():
        print(f"  {cat}: {len(metrics)} metrics")
        for m in metrics:
            print(f"    {m['name']}: {m['score']:.4f}")


if __name__ == "__main__":
    main()
