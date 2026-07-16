from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PerAgentLLMUsage:
    agent_name: str
    period: str = ""
    calls: int = 0
    models: dict = field(default_factory=dict)
    errors: dict = field(default_factory=lambda: defaultdict(int))
    fallbacks: dict = field(default_factory=lambda: defaultdict(int))
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    guardrail_block_rate: float = 0.0
    human_review_rate: float = 0.0


class LLMAnalyticsTracker:
    def __init__(self):
        self._agent_calls: dict[str, list[dict]] = defaultdict(list)
        self._agent_latencies: dict[str, list[float]] = defaultdict(list)
        self._agent_errors: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._agent_fallbacks: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._agent_guardrail_blocks: dict[str, int] = defaultdict(int)
        self._agent_human_reviews: dict[str, int] = defaultdict(int)

    def record_llm_call(
        self,
        agent_name: str,
        model: str,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        prompt_path: str = "",
        success: bool = True,
        error_type: str | None = None,
    ) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": agent_name,
            "model": model,
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "prompt_path": prompt_path,
            "success": success,
        }
        self._agent_calls[agent_name].append(record)
        self._agent_latencies[agent_name].append(latency_ms)

        if not success and error_type:
            self._agent_errors[agent_name][error_type] += 1

    def record_fallback(
        self,
        agent_name: str,
        from_model: str,
        to_model: str,
    ) -> None:
        key = f"{from_model}→{to_model}"
        self._agent_fallbacks[agent_name][key] += 1

    def record_guardrail_block(self, agent_name: str) -> None:
        self._agent_guardrail_blocks[agent_name] += 1

    def record_human_review(self, agent_name: str) -> None:
        self._agent_human_reviews[agent_name] += 1

    def get_report(self, agent_name: str) -> PerAgentLLMUsage:
        calls = self._agent_calls.get(agent_name, [])
        latencies = self._agent_latencies.get(agent_name, [])

        models: dict = {}
        for call in calls:
            model = call["model"]
            if model not in models:
                models[model] = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost": 0.0}
            models[model]["calls"] += 1
            models[model]["tokens_in"] += call["input_tokens"]
            models[model]["tokens_out"] += call["output_tokens"]

        total_calls = len(calls)

        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        sorted_latencies = sorted(latencies)
        p95_idx = int(len(sorted_latencies) * 0.95)
        p95_latency = sorted_latencies[p95_idx] if sorted_latencies else 0.0

        total_calls_or_1 = max(total_calls, 1)

        return PerAgentLLMUsage(
            agent_name=agent_name,
            period=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            calls=total_calls,
            models=models,
            errors=dict(self._agent_errors.get(agent_name, {})),
            fallbacks=dict(self._agent_fallbacks.get(agent_name, {})),
            avg_latency_ms=round(avg_latency, 2),
            p95_latency_ms=round(p95_latency, 2),
            guardrail_block_rate=round(
                self._agent_guardrail_blocks.get(agent_name, 0) / total_calls_or_1, 4
            ),
            human_review_rate=round(
                self._agent_human_reviews.get(agent_name, 0) / total_calls_or_1, 4
            ),
        )


llm_analytics = LLMAnalyticsTracker()
