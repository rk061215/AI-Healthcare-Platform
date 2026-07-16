from __future__ import annotations

import pytest

from app.tools.exceptions import ToolNotFoundError, ToolRegistrationError
from app.tools.tool_registry import ToolRegistry, get_global_registry
from tests.test_tools.conftest import SimpleTool


class TestToolRegistry:
    def setup_method(self):
        self.registry = ToolRegistry()

    def test_register_and_get(self):
        self.registry.register("simple", SimpleTool)
        cls = self.registry.get("simple")
        assert cls is SimpleTool

    def test_register_duplicate_raises(self):
        self.registry.register("simple", SimpleTool)
        with pytest.raises(ToolRegistrationError, match="already registered"):
            self.registry.register("simple", SimpleTool)

    def test_get_not_found(self):
        with pytest.raises(ToolNotFoundError, match="not registered"):
            self.registry.get("nonexistent")

    def test_unregister(self):
        self.registry.register("simple", SimpleTool)
        self.registry.unregister("simple")
        with pytest.raises(ToolNotFoundError):
            self.registry.get("simple")

    def test_unregister_nonexistent_no_error(self):
        self.registry.unregister("nonexistent")

    def test_list_tools(self):
        self.registry.register("a", SimpleTool)
        self.registry.register("b", SimpleTool)
        tools = self.registry.list_tools()
        assert "a" in tools
        assert "b" in tools
        assert len(tools) == 2

    def test_clear(self):
        self.registry.register("a", SimpleTool)
        self.registry.register("b", SimpleTool)
        self.registry.clear()
        assert self.registry.list_tools() == []

    def test_global_registry(self):
        registry1 = get_global_registry()
        registry2 = get_global_registry()
        assert registry1 is registry2
