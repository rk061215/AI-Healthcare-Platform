from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.validation.benchmark.benchmark_suite import BenchmarkResult


class BenchmarkHistory:
    def __init__(self, storage_dir: str | Path = "benchmark_results"):
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def save_result(self, result: BenchmarkResult) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        fname = f"{result.config_name}_{ts}.json"
        path = self._storage_dir / fname
        data = {
            "config_name": result.config_name,
            "timestamp": result.timestamp or ts,
            "overall_scores": result.overall_scores,
            "per_question_scores": result.per_question_scores,
            "latency_stats": result.latency_stats,
            "memory_stats": result.memory_stats,
            "token_stats": result.token_stats,
            "errors": result.errors,
            "questions_attempted": result.questions_attempted,
            "questions_succeeded": result.questions_succeeded,
            "metadata": result.metadata,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return str(path)

    def load_result(self, path: str | Path) -> Optional[BenchmarkResult]:
        p = Path(path)
        if not p.exists():
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return BenchmarkResult(
                config_name=data.get("config_name", ""),
                timestamp=data.get("timestamp", ""),
                overall_scores=data.get("overall_scores", {}),
                per_question_scores=data.get("per_question_scores", []),
                latency_stats=data.get("latency_stats", {}),
                memory_stats=data.get("memory_stats", {}),
                token_stats=data.get("token_stats", {}),
                errors=data.get("errors", []),
                questions_attempted=data.get("questions_attempted", 0),
                questions_succeeded=data.get("questions_succeeded", 0),
                metadata=data.get("metadata", {}),
            )
        except Exception:
            return None

    def list_history(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for fpath in sorted(self._storage_dir.glob("*.json")):
            try:
                result = self.load_result(fpath)
                if result is not None:
                    results.append({
                        "path": str(fpath),
                        "name": fpath.stem,
                        "config_name": result.config_name,
                        "timestamp": result.timestamp,
                        "questions_attempted": result.questions_attempted,
                        "questions_succeeded": result.questions_succeeded,
                        "modified": fpath.stat().st_mtime,
                    })
            except Exception:
                continue
        return sorted(results, key=lambda x: x["modified"], reverse=True)

    def get_latest(self, config_name: str) -> Optional[BenchmarkResult]:
        best: Optional[BenchmarkResult] = None
        best_ts = ""
        for fpath in self._storage_dir.glob(f"{config_name}_*.json"):
            result = self.load_result(fpath)
            if result is not None and result.timestamp > best_ts:
                best = result
                best_ts = result.timestamp
        return best

    def compare(self, result_a: BenchmarkResult, result_b: BenchmarkResult) -> dict[str, Any]:
        comparison: dict[str, Any] = {}
        all_keys = set(result_a.overall_scores.keys()) | set(result_b.overall_scores.keys())
        for key in sorted(all_keys):
            va = result_a.overall_scores.get(key, 0)
            vb = result_b.overall_scores.get(key, 0)
            diff = vb - va
            comparison[key] = {
                "baseline": va,
                "current": vb,
                "diff": diff,
                "pct_change": (diff / va * 100) if va != 0 else 0,
                "regression": diff < -0.01,
            }
        return comparison
