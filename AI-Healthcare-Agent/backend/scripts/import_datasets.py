"""
CLI script to import datasets from JSON/JSONL files into the DatasetManager.

Usage:
    python scripts/import_datasets.py
    python scripts/import_datasets.py --dir datasets/
    python scripts/import_datasets.py --validate-only
    python scripts/import_datasets.py --list
    python scripts/import_datasets.py --stats
"""

import argparse
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.validation import DatasetLoader, DatasetValidator, DatasetManager


def list_datasets(manager: DatasetManager) -> None:
    datasets = manager.list_datasets()
    if not datasets:
        print("No datasets found in storage.")
        return
    print(f"{'Name':<30} {'Version':<12} {'Docs':<6} {'Entries':<8} {'Description'}")
    print("-" * 90)
    for ds in datasets:
        if ds.get("error"):
            print(f"{ds['name']:<30} {'ERROR':<12} {'-':<6} {'-':<8} {ds.get('path', '')}")
        else:
            print(
                f"{ds['name']:<30} "
                f"{ds['version']:<12} "
                f"{ds['documents']:<6} "
                f"{ds['entries']:<8} "
                f"{ds['description']}"
            )


def show_stats(manager: DatasetManager) -> None:
    datasets = manager.list_datasets()
    if not datasets:
        print("No datasets in storage to show stats for.")
        return

    total_docs = 0
    total_entries = 0
    for ds in datasets:
        if not ds.get("error"):
            total_docs += ds.get("documents", 0)
            total_entries += ds.get("entries", 0)

    print(f"Total datasets: {len(datasets)}")
    print(f"Total documents: {total_docs}")
    print(f"Total entries: {total_entries}")
    print()

    for ds in datasets:
        if ds.get("error"):
            continue
        name = ds["name"]
        stats = manager.get_stats(name)
        if stats is None:
            continue
        by_diff = stats.get("by_difficulty", {})
        by_cat = stats.get("by_category", {})
        by_dt = stats.get("by_document_type", {})

        print(f"  [{name}]")
        print(f"    Documents: {stats['total_documents']}, Entries: {stats['total_entries']}")
        if by_diff:
            parts = " | ".join(f"{k}: {v}" for k, v in sorted(by_diff.items()))
            print(f"    By difficulty: {parts}")
        if by_cat:
            parts = " | ".join(f"{k}: {v}" for k, v in sorted(by_cat.items()))
            print(f"    By category: {parts}")
        if by_dt:
            parts = " | ".join(f"{k}: {v}" for k, v in sorted(by_dt.items()))
            print(f"    By document type: {parts}")
        print()


def import_datasets(source_dir: str, manager: DatasetManager, validate_only: bool) -> None:
    src = Path(source_dir)
    if not src.is_dir():
        print(f"Error: {source_dir} is not a valid directory.")
        sys.exit(1)

    files = sorted(src.rglob("*"))
    json_files = [f for f in files if f.suffix in (".json", ".jsonl")]

    if not json_files:
        print(f"No JSON or JSONL files found in {source_dir}")
        return

    results = []

    for fpath in json_files:
        rel = fpath.relative_to(src)
        print(f"Processing: {rel} ... ", end="")

        try:
            if fpath.suffix == ".jsonl":
                gt_sets = DatasetLoader.load_jsonl(fpath)
            else:
                singleton = DatasetLoader.load_json(fpath)
                gt_sets = [singleton]
        except Exception as e:
            print(f"FAILED to load: {e}")
            results.append({
                "file": str(rel),
                "status": "load_error",
                "error": str(e),
            })
            continue

        for i, gt_set in enumerate(gt_sets):
            suffix = f" (part {i + 1})" if len(gt_sets) > 1 else ""
            name = gt_set.name or fpath.stem

            val_result = DatasetValidator.validate(gt_set)
            if not val_result.is_valid:
                print(f"INVALID{suffix}")
                for err in val_result.errors:
                    print(f"    Error: {err}")
                results.append({
                    "file": str(rel),
                    "name": name,
                    "status": "invalid",
                    "errors": val_result.errors,
                    "warnings": val_result.warnings,
                })
                continue

            if validate_only:
                print(f"VALID{suffix}")
                results.append({
                    "file": str(rel),
                    "name": name,
                    "status": "valid",
                    "warnings": val_result.warnings,
                })
                continue

            try:
                saved_path = manager.save_dataset(gt_set, name=name)
                print(f"IMPORTED{suffix} -> {saved_path}")
                results.append({
                    "file": str(rel),
                    "name": name,
                    "status": "imported",
                    "path": saved_path,
                    "documents": len(gt_set.documents),
                    "entries": gt_set.count(),
                    "warnings": val_result.warnings,
                })
            except Exception as e:
                print(f"FAILED to save{suffix}: {e}")
                results.append({
                    "file": str(rel),
                    "name": name,
                    "status": "save_error",
                    "error": str(e),
                })

    print()
    print("=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)

    headers = ["File", "Dataset", "Status", "Docs", "Entries"]
    col_widths = [40, 25, 12, 6, 8]
    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))

    counts = {"imported": 0, "valid": 0, "invalid": 0, "load_error": 0, "save_error": 0}
    for r in results:
        status = r["status"]
        counts[status] = counts.get(status, 0) + 1
        docs = r.get("documents", "-")
        entries = r.get("entries", "-")
        row = [
            r["file"][:40].ljust(40),
            r.get("name", "-")[:25].ljust(25),
            status.ljust(12),
            str(docs).ljust(6),
            str(entries).ljust(8),
        ]
        print(" | ".join(row))

    print("-" * len(header_line))
    print(f"Total: {len(results)} files")
    for st, cnt in counts.items():
        if cnt:
            print(f"  {st}: {cnt}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import datasets into DatasetManager storage")
    parser.add_argument("--dir", default="datasets", help="Directory to scan for dataset files (default: datasets/)")
    parser.add_argument("--validate-only", action="store_true", help="Only validate, do not save")
    parser.add_argument("--list", action="store_true", help="List already-imported datasets")
    parser.add_argument("--stats", action="store_true", help="Show statistics for imported datasets")
    parser.add_argument("--storage-dir", default="datasets", help="DatasetManager storage directory (default: datasets/)")

    args = parser.parse_args()

    manager = DatasetManager(storage_dir=args.storage_dir)

    if args.list:
        list_datasets(manager)
        return

    if args.stats:
        show_stats(manager)
        return

    import_datasets(args.dir, manager, args.validate_only)


if __name__ == "__main__":
    main()
