"""
CLI script to run a batch benchmark on a dataset.

Usage:
    python scripts/run_batch_benchmark.py --dataset sample_golden_qa
    python scripts/run_batch_benchmark.py --dataset sample_golden_qa --real-llm
    python scripts/run_batch_benchmark.py --dataset sample_golden_qa --top-k 10 --questions-limit 20
    python scripts/run_batch_benchmark.py --dataset sample_golden_qa --output-dir my_results
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.validation import (
    DatasetLoader,
    DatasetManager,
    BenchmarkConfig,
    BenchmarkRunner,
)
from app.validation.benchmark.benchmark_suite import BenchmarkResult


def build_mock_answer_fn(dataset_name: str):
    def mock_answer_fn(question: str) -> dict:
        time.sleep(0.05)
        return {
            "answer": (
                f"This is a mock answer for question: {question}. "
                f"Replace with --real-llm to use an actual LLM."
            ),
            "sources": ["mock_source_1", "mock_source_2"],
            "token_count": len(question.split()) * 5 + 20,
        }

    return mock_answer_fn


def load_questions(dataset_name: str, dataset_path: str | None, questions_limit: int | None) -> tuple[list[str], str]:
    if dataset_path:
        p = Path(dataset_path)
        if not p.exists():
            print(f"Error: dataset path not found: {p}")
            sys.exit(1)
        if p.suffix == ".jsonl":
            gt_sets = DatasetLoader.load_jsonl(p)
            gt_set = gt_sets[0] if gt_sets else None
        else:
            gt_set = DatasetLoader.load_json(p)
        source_desc = str(p)
    else:
        manager = DatasetManager()
        gt_set = manager.load_dataset(dataset_name)
        source_desc = dataset_name

    if gt_set is None:
        print(f"Error: dataset '{dataset_name}' not found.")
        sys.exit(1)

    entries = gt_set.all_entries()
    if not entries:
        print(f"Error: dataset '{gt_set.name}' has no entries.")
        sys.exit(1)

    questions = [e.question for e in entries]

    if questions_limit and questions_limit < len(questions):
        questions = questions[:questions_limit]
        print(f"Limited to {questions_limit} questions.")

    print(f"Loaded {len(questions)} questions from '{source_desc}'")
    return questions, gt_set.name


def generate_reports(result: BenchmarkResult, output_dir: str, config: BenchmarkConfig) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    summary = result.summary()

    json_path = out / f"benchmark_{config.name}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "config": config.dict(),
            "result": summary,
            "per_question_scores": result.per_question_scores,
        }, f, indent=2, default=str)
    print(f"JSON report: {json_path}")

    md_path = out / f"benchmark_{config.name}.md"
    ts = result.timestamp
    scores = result.overall_scores
    latency = result.latency_stats
    memory = result.memory_stats
    tokens = result.token_stats

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Benchmark Report: {config.name}\n\n")
        f.write(f"> Generated: {ts}\n\n")

        f.write("## Configuration\n\n")
        f.write(f"| Setting | Value |\n|--------|-------|\n")
        f.write(f"| Dataset | {config.dataset_name} |\n")
        f.write(f"| Top-K | {config.top_k} |\n")
        f.write(f"| Questions | {result.questions_attempted} |\n")
        f.write(f"| Real LLM | {config.dict().get('real_llm', False)} |\n\n")

        f.write("## Results\n\n")
        f.write("| Metric | Value |\n|--------|-------|\n")
        f.write(f"| Attempted | {result.questions_attempted} |\n")
        f.write(f"| Succeeded | {result.questions_succeeded} |\n")
        f.write(f"| Success Rate | {result.success_rate():.1%} |\n")

        if scores:
            f.write("\n## Overall Scores\n\n")
            f.write("| Metric | Value |\n|--------|-------|\n")
            for key in sorted(scores.keys()):
                f.write(f"| {key} | {scores[key]:.4f} |\n")

        if latency:
            f.write("\n## Latency\n\n")
            f.write("| Metric | Value |\n|--------|-------|\n")
            for key in ("mean", "median", "p95", "p99", "min", "max"):
                if key in latency:
                    f.write(f"| {key} | {latency[key]:.1f} ms |\n")

        if memory:
            f.write("\n## Memory\n\n")
            f.write("| Metric | Value |\n|--------|-------|\n")
            f.write(f"| Mean | {memory.get('mean_mb', memory.get('mean', 0)):.1f} MB |\n")
            f.write(f"| Peak | {memory.get('peak_mb', memory.get('max', 0)):.1f} MB |\n")

        if tokens:
            f.write("\n## Token Usage\n\n")
            f.write("| Metric | Value |\n|--------|-------|\n")
            f.write(f"| Total | {tokens.get('total', 0):.0f} |\n")
            f.write(f"| Mean | {tokens.get('mean', 0):.0f} |\n")

        if result.errors:
            f.write("\n## Errors\n\n")
            for err in result.errors[:20]:
                f.write(f"- {err}\n")

    print(f"Markdown report: {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a batch benchmark on a dataset")
    parser.add_argument("--dataset", required=True, help="Dataset name (or path with --dataset-path)")
    parser.add_argument("--dataset-path", help="Direct path to a dataset file (bypasses DatasetManager)")
    parser.add_argument("--output-dir", default="benchmark_results", help="Output directory for reports")
    parser.add_argument("--top-k", type=int, default=5, help="Top-K retrieval count (default: 5)")
    parser.add_argument("--questions-limit", type=int, default=None, help="Limit number of questions to run")
    parser.add_argument("--real-llm", action="store_true", help="Use a real LLM (default: mock)")

    args = parser.parse_args()

    questions, resolved_name = load_questions(args.dataset, args.dataset_path, args.questions_limit)

    config = BenchmarkConfig(
        name=f"{resolved_name}_benchmark",
        description=f"Benchmark for dataset {resolved_name}",
        dataset_name=resolved_name,
        dataset_path=args.dataset_path or "",
        top_k=args.top_k,
        max_questions=args.questions_limit,
        output_dir=args.output_dir,
    )

    runner = BenchmarkRunner(config=config)

    if args.real_llm:
        print("WARNING: --real-llm flag set but no LLM integration is wired up.")
        print("Falling back to mock answer function. Wire your LLM client into the answer_fn.")

    answer_fn = build_mock_answer_fn(resolved_name)

    print(f"Running benchmark '{config.name}' with {len(questions)} questions ...")
    result = runner.run(questions, answer_fn)

    summary = result.summary()
    print(f"\nBenchmark complete:")
    print(f"  Attempted: {summary['questions_attempted']}")
    print(f"  Succeeded: {summary['questions_succeeded']}")
    print(f"  Success rate: {summary['success_rate']:.1%}")
    if summary.get("overall_scores"):
        for key, val in summary["overall_scores"].items():
            print(f"  {key}: {val:.4f}")

    generate_reports(result, args.output_dir, config)

    print(f"\nResults also saved to benchmark history at: {config.output_dir}")


if __name__ == "__main__":
    main()
