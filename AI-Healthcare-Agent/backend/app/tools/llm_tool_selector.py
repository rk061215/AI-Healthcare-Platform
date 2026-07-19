from __future__ import annotations

import json
from typing import Any, Optional

from app.ai.config import AIProviderConfig
from app.ai.provider_factory import AIProviderFactory
from app.tools.exceptions import ToolSelectorError
from app.tools.tool_registry import get_global_registry
from app.tools.tool_selector import ToolSelector

TOOL_SELECTION_PROMPT = """Given the user's medical query and the available tools, select the best tool and action.

Available tools:
{tools_list}

User query: {query}

Return a JSON object with:
{{
  "tool_name": "selected tool name or null",
  "action": "selected action or null",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}

If no tool is relevant, set tool_name and action to null."""


class LLMToolSelector:
    def __init__(
        self,
        provider_factory: Optional[AIProviderFactory] = None,
        provider: str = "gemini",
        model: str = "gemini-2.0-flash",
        fallback_selector: Optional[ToolSelector] = None,
    ):
        self._provider_factory = provider_factory
        self._provider_name = provider
        self._model = model
        self._fallback = fallback_selector or ToolSelector()
        self._llm = None

    def _lazy_init(self) -> None:
        if self._llm is not None:
            return
        config = AIProviderConfig(
            provider=self._provider_name,
            model=self._model,
            temperature=0.1,
            max_tokens=256,
        )
        if self._provider_factory:
            self._llm = self._provider_factory.create(config)
        else:
            self._llm = AIProviderFactory.create(config)

    def select(self, query: str) -> tuple[str, str]:
        try:
            result = self._llm_select(query)
            if result:
                return result
        except Exception:
            pass
        return self._fallback.select(query)

    def select_or_none(self, query: str) -> Optional[tuple[str, str]]:
        try:
            return self.select(query)
        except ToolSelectorError:
            return None

    def _llm_select(self, query: str) -> Optional[tuple[str, str]]:
        self._lazy_init()

        registry = get_global_registry()
        all_tools = registry.list_tools()
        tools_list = "\n".join(
            f"- {name}: {cls.__doc__ or 'No description'}"
            for name, cls in all_tools.items()
        )

        prompt = TOOL_SELECTION_PROMPT.format(
            tools_list=tools_list or "No tools registered",
            query=query,
        )

        try:
            result = self._llm.generate_structured_output(
                prompt=prompt,
                output_schema={
                    "type": "object",
                    "properties": {
                        "tool_name": {"type": "string"},
                        "action": {"type": "string"},
                        "confidence": {"type": "number"},
                        "reasoning": {"type": "string"},
                    },
                    "required": ["tool_name", "action"],
                },
            )
            tool_name = result.get("tool_name")
            action = result.get("action")
            if tool_name and action and tool_name != "null":
                return tool_name.strip(), action.strip()
        except Exception:
            pass

        return None
