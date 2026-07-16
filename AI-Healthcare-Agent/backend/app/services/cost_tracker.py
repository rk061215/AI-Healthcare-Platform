from prometheus_client import Counter, Gauge

from app.core.config import settings

llm_cost_total = Counter(
    "llm_cost_total",
    "Cumulative LLM cost in USD",
    ["model", "agent_name"],
)

llm_cost_daily = Gauge(
    "llm_cost_daily",
    "Daily LLM cost in USD",
)

llm_cost_per_request = Gauge(
    "llm_cost_per_request",
    "Cost per individual LLM request",
    ["agent_name"],
)

llm_tokens_input_total = Counter(
    "llm_tokens_input_total",
    "Cumulative input tokens consumed",
    ["model"],
)

llm_tokens_output_total = Counter(
    "llm_tokens_output_total",
    "Cumulative output tokens consumed",
    ["model"],
)

MODEL_COST_PER_1K_INPUT: dict[str, float] = {
    "gpt-4o": 0.01,
    "gpt-4o-mini": 0.0015,
    "gpt-4": 0.03,
    "gpt-3.5-turbo": 0.0005,
    "text-embedding-3-small": 0.00002,
}

MODEL_COST_PER_1K_OUTPUT: dict[str, float] = {
    "gpt-4o": 0.03,
    "gpt-4o-mini": 0.006,
    "gpt-4": 0.06,
    "gpt-3.5-turbo": 0.0015,
    "text-embedding-3-small": 0.0,
}


class CostTracker:
    def __init__(self):
        self._daily_cost = 0.0

    def track_llm_call(
        self,
        model: str,
        agent_name: str = "unknown",
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> float:
        model_key = model if model in MODEL_COST_PER_1K_INPUT else "gpt-4o-mini"
        input_cost = (input_tokens / 1000) * MODEL_COST_PER_1K_INPUT.get(model_key, 0)
        output_cost = (output_tokens / 1000) * MODEL_COST_PER_1K_OUTPUT.get(model_key, 0)
        total_cost = round(input_cost + output_cost, 6)

        llm_cost_total.labels(model=model_key, agent_name=agent_name).inc(total_cost)
        llm_cost_per_request.labels(agent_name=agent_name).set(total_cost)
        llm_tokens_input_total.labels(model=model_key).inc(input_tokens)
        llm_tokens_output_total.labels(model=model_key).inc(output_tokens)

        self._daily_cost += total_cost
        llm_cost_daily.set(self._daily_cost)

        return total_cost

    def reset_daily_cost(self) -> None:
        self._daily_cost = 0.0
        llm_cost_daily.set(0.0)


cost_tracker = CostTracker()
