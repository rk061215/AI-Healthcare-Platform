from __future__ import annotations

from typing import Optional

from app.context.config import ContextConfig
from app.context.exceptions import ConfigurationError
from app.context.models import ContextFragment, TokenUsageInfo


# Rough estimate: ~4 characters per token for medical text
CHARS_PER_TOKEN = 4.0


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / CHARS_PER_TOKEN))


def estimate_fragment_tokens(fragment: ContextFragment) -> int:
    return estimate_tokens(fragment.text)


class TokenBudgetManager:
    """Manages token budgets with configurable strategies.

    Strategies:
    - fixed_max: Hard cap on total tokens
    - priority_truncation: Remove lowest-priority fragments when over budget
    - section_preserve: Keep complete medical sections where possible
    """

    def __init__(self, config: Optional[ContextConfig] = None) -> None:
        self._config = config or ContextConfig()

    def enforce_budget(
        self,
        fragments: list[ContextFragment],
        max_tokens: Optional[int] = None,
    ) -> tuple[list[ContextFragment], TokenUsageInfo]:
        if not fragments:
            return [], TokenUsageInfo()

        budget = max_tokens or self._config.max_tokens
        strategy = self._config.strategy

        if strategy == "fixed_max":
            return self._fixed_max(fragments, budget)
        elif strategy == "priority_truncation":
            return self._priority_truncation(fragments, budget)
        elif strategy == "section_preserve":
            return self._section_preserve(fragments, budget)
        else:
            raise ConfigurationError(f"Unknown token budget strategy: {strategy}")

    def _fixed_max(
        self,
        fragments: list[ContextFragment],
        max_tokens: int,
    ) -> tuple[list[ContextFragment], TokenUsageInfo]:
        selected: list[ContextFragment] = []
        total_tokens = 0
        truncated = False

        for frag in fragments:
            tokens = estimate_fragment_tokens(frag)
            if total_tokens + tokens > max_tokens:
                truncated = True
                break
            selected.append(frag)
            total_tokens += tokens

        return selected, TokenUsageInfo(
            estimated_tokens=total_tokens,
            max_allowed_tokens=max_tokens,
            remaining_tokens=max_tokens - total_tokens,
            truncated=truncated,
            fragments_count=len(selected),
            strategy="fixed_max",
        )

    def _priority_truncation(
        self,
        fragments: list[ContextFragment],
        max_tokens: int,
    ) -> tuple[list[ContextFragment], TokenUsageInfo]:
        selected: list[ContextFragment] = []
        total_tokens = 0
        truncated = False

        prioritized = self._prioritize_fragments(fragments)
        for frag in prioritized:
            tokens = estimate_fragment_tokens(frag)
            if total_tokens + tokens > max_tokens:
                truncated = True
                continue
            selected.append(frag)
            total_tokens += tokens

        selected.sort(key=lambda f: f.rank)
        return selected, TokenUsageInfo(
            estimated_tokens=total_tokens,
            max_allowed_tokens=max_tokens,
            remaining_tokens=max_tokens - total_tokens,
            truncated=truncated,
            fragments_count=len(selected),
            strategy="priority_truncation",
        )

    def _section_preserve(
        self,
        fragments: list[ContextFragment],
        max_tokens: int,
    ) -> tuple[list[ContextFragment], TokenUsageInfo]:
        grouped: dict[str, list[ContextFragment]] = {}
        for frag in fragments:
            section = frag.citation.section or "other"
            grouped.setdefault(section, []).append(frag)

        selected: list[ContextFragment] = []
        total_tokens = 0
        truncated = False

        for section in self._config.section_order:
            if section not in grouped:
                continue
            section_frags = grouped.pop(section)
            section_tokens = sum(estimate_fragment_tokens(f) for f in section_frags)

            if total_tokens + section_tokens <= max_tokens:
                selected.extend(section_frags)
                total_tokens += section_tokens
            else:
                remaining = max_tokens - total_tokens
                for frag in section_frags:
                    tokens = estimate_fragment_tokens(frag)
                    if tokens <= remaining:
                        selected.append(frag)
                        total_tokens += tokens
                        remaining -= tokens
                    else:
                        truncated = True

        for section, section_frags in grouped.items():
            for frag in section_frags:
                tokens = estimate_fragment_tokens(frag)
                if total_tokens + tokens <= max_tokens:
                    selected.append(frag)
                    total_tokens += tokens
                else:
                    truncated = True
                    break

        return selected, TokenUsageInfo(
            estimated_tokens=total_tokens,
            max_allowed_tokens=max_tokens,
            remaining_tokens=max_tokens - total_tokens,
            truncated=truncated,
            fragments_count=len(selected),
            strategy="section_preserve",
        )

    def _prioritize_fragments(
        self,
        fragments: list[ContextFragment],
    ) -> list[ContextFragment]:
        priority_sections = list(self._config.priority_sections)

        def sort_key(f: ContextFragment) -> tuple[int, float]:
            section = f.citation.section or ""
            if section in priority_sections:
                idx = priority_sections.index(section)
            else:
                idx = len(priority_sections)
            return (idx, -f.score)

        return sorted(fragments, key=sort_key)
