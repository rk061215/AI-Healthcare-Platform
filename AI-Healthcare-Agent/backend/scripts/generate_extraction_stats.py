"""
CLI script to generate comprehensive extraction statistics across all datasets.

Usage:
    python scripts/generate_extraction_stats.py
    python scripts/generate_extraction_stats.py --output-dir stats_output
    python scripts/generate_extraction_stats.py --dataset sample_golden_qa
"""

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.validation import DatasetManager
from app.validation.dataset.ground_truth import (
    DifficultyLevel,
    DocumentType,
    GroundTruthSet,
    QuestionCategory,
)


def collect_all_datasets(manager: DatasetManager, dataset_filter: str | None) -> dict[str, GroundTruthSet]:
    datasets: dict[str, GroundTruthSet] = {}
    for entry in manager.list_datasets():
        name = entry["name"]
        if dataset_filter and name != dataset_filter:
            continue
        gt_set = manager.load_dataset(name)
        if gt_set is not None:
            datasets[name] = gt_set
    return datasets


def compute_stats(datasets: dict[str, GroundTruthSet]) -> dict[str, Any]:
    total_docs = 0
    total_entries = 0

    doc_type_counter: Counter = Counter()
    difficulty_counter: Counter = Counter()
    category_counter: Counter = Counter()
    confidence_values: list[float] = []
    entries_with_notes = 0
    entries_with_citations = 0
    entries_with_concepts = 0

    per_dataset: dict[str, Any] = {}

    for name, gt_set in datasets.items():
        ds_docs = len(gt_set.documents)
        ds_entries = gt_set.count()
        total_docs += ds_docs
        total_entries += ds_entries

        ds_doc_types: Counter = Counter()
        ds_difficulty: Counter = Counter()
        ds_category: Counter = Counter()
        ds_conf: list[float] = []

        for doc in gt_set.documents:
            dt = doc.document_type.value
            doc_type_counter[dt] += 1
            ds_doc_types[dt] += 1

            for entry in doc.entries:
                diff = entry.difficulty.value
                cat = entry.category.value

                difficulty_counter[diff] += 1
                category_counter[cat] += 1
                ds_difficulty[diff] += 1
                ds_category[cat] += 1

                confidence_values.append(entry.expected_confidence)
                ds_conf.append(entry.expected_confidence)

                if entry.notes:
                    entries_with_notes += 1
                if entry.expected_citations:
                    entries_with_citations += 1
                if entry.expected_medical_concepts:
                    entries_with_concepts += 1

        per_dataset[name] = {
            "documents": ds_docs,
            "entries": ds_entries,
            "by_document_type": dict(ds_doc_types),
            "by_difficulty": dict(ds_difficulty),
            "by_category": dict(ds_category),
            "confidence": {
                "mean": round(sum(ds_conf) / len(ds_conf), 4) if ds_conf else 0,
                "min": round(min(ds_conf), 4) if ds_conf else 0,
                "max": round(max(ds_conf), 4) if ds_conf else 0,
            },
        }

    all_doc_types = set(dt.value for dt in DocumentType)
    covered_doc_types = set(doc_type_counter.keys())
    uncovered_doc_types = all_doc_types - covered_doc_types

    all_categories = set(qc.value for qc in QuestionCategory)
    covered_categories = set(category_counter.keys())
    uncovered_categories = all_categories - covered_categories

    all_difficulties = set(dl.value for dl in DifficultyLevel)
    covered_difficulties = set(difficulty_counter.keys())
    uncovered_difficulties = all_difficulties - covered_difficulties

    mean_conf = (sum(confidence_values) / len(confidence_values)) if confidence_values else 0
    conf_by_bucket = {
        "0.0-0.5": sum(1 for v in confidence_values if v < 0.5),
        "0.5-0.7": sum(1 for v in confidence_values if 0.5 <= v < 0.7),
        "0.7-0.9": sum(1 for v in confidence_values if 0.7 <= v < 0.9),
        "0.9-1.0": sum(1 for v in confidence_values if v >= 0.9),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_count": len(datasets),
        "total_documents": total_docs,
        "total_entries": total_entries,
        "documents_by_type": dict(doc_type_counter),
        "entries_by_difficulty": dict(difficulty_counter),
        "entries_by_category": dict(category_counter),
        "confidence": {
            "mean": round(mean_conf, 4),
            "min": round(min(confidence_values), 4) if confidence_values else 0,
            "max": round(max(confidence_values), 4) if confidence_values else 0,
            "distribution": conf_by_bucket,
        },
        "coverage_gaps": {
            "uncovered_document_types": sorted(uncovered_doc_types),
            "uncovered_categories": sorted(uncovered_categories),
            "uncovered_difficulties": sorted(uncovered_difficulties),
            "covered_document_types": sorted(covered_doc_types),
            "covered_categories": sorted(covered_categories),
            "covered_difficulties": sorted(covered_difficulties),
            "document_type_coverage_pct": round(
                len(covered_doc_types) / len(all_doc_types) * 100, 1
            ) if all_doc_types else 0,
            "category_coverage_pct": round(
                len(covered_categories) / len(all_categories) * 100, 1
            ) if all_categories else 0,
            "difficulty_coverage_pct": round(
                len(covered_difficulties) / len(all_difficulties) * 100, 1
            ) if all_difficulties else 0,
        },
        "entry_quality": {
            "entries_with_citations": entries_with_citations,
            "entries_with_medical_concepts": entries_with_concepts,
            "entries_with_notes": entries_with_notes,
            "pct_with_citations": round(
                entries_with_citations / total_entries * 100, 1
            ) if total_entries else 0,
            "pct_with_concepts": round(
                entries_with_concepts / total_entries * 100, 1
            ) if total_entries else 0,
        },
        "per_dataset": per_dataset,
    }


def write_json_report(stats: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "extraction_stats.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, default=str)
    return path


def write_markdown_report(stats: dict[str, Any], output_dir: Path) -> Path:
    path = output_dir / "extraction_stats_report.md"
    cov = stats["coverage_gaps"]
    conf = stats["confidence"]
    quality = stats["entry_quality"]

    lines = [
        "# Extraction Statistics Report",
        "",
        f"> Generated: {stats['generated_at']}",
        "",
        "## Overview",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Datasets | {stats['dataset_count']} |",
        f"| Total Documents | {stats['total_documents']} |",
        f"| Total Entries | {stats['total_entries']} |",
        "",
        "## Documents by Type",
        "",
    ]

    if stats["documents_by_type"]:
        lines.append("| Document Type | Count |")
        lines.append("|--------------|-------|")
        for dt, cnt in sorted(stats["documents_by_type"].items()):
            lines.append(f"| {dt} | {cnt} |")
    else:
        lines.append("No documents found.")

    lines += [
        "",
        "## Entries by Difficulty",
        "",
    ]

    if stats["entries_by_difficulty"]:
        lines.append("| Difficulty | Count |")
        lines.append("|------------|-------|")
        for diff, cnt in sorted(stats["entries_by_difficulty"].items()):
            lines.append(f"| {diff} | {cnt} |")
    else:
        lines.append("No entries found.")

    lines += [
        "",
        "## Entries by Category",
        "",
    ]

    if stats["entries_by_category"]:
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        for cat, cnt in sorted(stats["entries_by_category"].items()):
            lines.append(f"| {cat} | {cnt} |")
    else:
        lines.append("No entries found.")

    lines += [
        "",
        "## Confidence Distribution",
        "",
        "| Range | Count |",
        "|-------|-------|",
    ]
    for bucket, cnt in conf["distribution"].items():
        lines.append(f"| {bucket} | {cnt} |")
    lines += [
        "",
        f"- Mean confidence: {conf['mean']}",
        f"- Min confidence: {conf['min']}",
        f"- Max confidence: {conf['max']}",
        "",
        "## Coverage Gaps",
        "",
        f"- Document type coverage: {cov['document_type_coverage_pct']}%",
        f"- Category coverage: {cov['category_coverage_pct']}%",
        f"- Difficulty coverage: {cov['difficulty_coverage_pct']}%",
        "",
    ]

    if cov["uncovered_document_types"]:
        lines.append(f"- Uncovered document types: {', '.join(cov['uncovered_document_types'])}")
    else:
        lines.append("- All document types are covered.")

    if cov["uncovered_categories"]:
        lines.append(f"- Uncovered categories: {', '.join(cov['uncovered_categories'])}")
    else:
        lines.append("- All question categories are covered.")

    if cov["uncovered_difficulties"]:
        lines.append(f"- Uncovered difficulties: {', '.join(cov['uncovered_difficulties'])}")
    else:
        lines.append("- All difficulty levels are covered.")

    lines += [
        "",
        "## Entry Quality",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Entries with citations | {quality['entries_with_citations']} ({quality['pct_with_citations']}%) |",
        f"| Entries with medical concepts | {quality['entries_with_concepts']} ({quality['pct_with_concepts']}%) |",
        f"| Entries with notes | {quality['entries_with_notes']} |",
        "",
    ]

    if stats["per_dataset"]:
        lines.append("## Per-Dataset Breakdown")
        lines.append("")
        for ds_name, ds_stats in stats["per_dataset"].items():
            lines.append(f"### {ds_name}")
            lines.append("")
            lines.append(f"- Documents: {ds_stats['documents']}")
            lines.append(f"- Entries: {ds_stats['entries']}")
            if ds_stats["by_difficulty"]:
                parts = " | ".join(f"{k}: {v}" for k, v in sorted(ds_stats["by_difficulty"].items()))
                lines.append(f"- By difficulty: {parts}")
            if ds_stats["by_category"]:
                parts = " | ".join(f"{k}: {v}" for k, v in sorted(ds_stats["by_category"].items()))
                lines.append(f"- By category: {parts}")
            lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate comprehensive extraction statistics across all datasets")
    parser.add_argument("--output-dir", default="extraction_stats", help="Output directory for reports (default: extraction_stats/)")
    parser.add_argument("--dataset", help="Only process a specific dataset by name")
    parser.add_argument("--storage-dir", default="datasets", help="DatasetManager storage directory (default: datasets/)")

    args = parser.parse_args()

    manager = DatasetManager(storage_dir=args.storage_dir)

    print("Loading datasets ...")
    datasets = collect_all_datasets(manager, args.dataset)

    if not datasets:
        print("Error: No datasets found to analyze.")
        sys.exit(1)

    print(f"Analyzing {len(datasets)} dataset(s) ...")
    stats = compute_stats(datasets)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = write_json_report(stats, output_dir)
    print(f"JSON stats: {json_path}")

    md_path = write_markdown_report(stats, output_dir)
    print(f"Markdown report: {md_path}")

    cov = stats["coverage_gaps"]
    print()
    print("Coverage Summary:")
    print(f"  Document types: {cov['document_type_coverage_pct']}% ({len(cov['covered_document_types'])}/{len(cov['covered_document_types']) + len(cov['uncovered_document_types'])})")
    print(f"  Categories:     {cov['category_coverage_pct']}% ({len(cov['covered_categories'])}/{len(cov['covered_categories']) + len(cov['uncovered_categories'])})")
    print(f"  Difficulties:   {cov['difficulty_coverage_pct']}% ({len(cov['covered_difficulties'])}/{len(cov['covered_difficulties']) + len(cov['uncovered_difficulties'])})")
    print(f"  Confidence mean: {stats['confidence']['mean']}")


if __name__ == "__main__":
    main()
