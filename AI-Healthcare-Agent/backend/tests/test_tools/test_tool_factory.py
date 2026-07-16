from __future__ import annotations

import pytest

from app.tools.config import ToolConfig
from app.tools.exceptions import ToolNotFoundError
from app.tools.tool_factory import ToolFactory
from app.tools.tool_registry import get_global_registry


class TestToolFactory:
    def test_create_existing(self):
        tool = ToolFactory.create("appointment")
        assert tool is not None

    def test_create_unknown_raises(self):
        with pytest.raises(ToolNotFoundError, match="not registered"):
            ToolFactory.create("nonexistent")

    def test_create_or_none_known(self):
        tool = ToolFactory.create_or_none("patient")
        assert tool is not None

    def test_create_or_none_unknown(self):
        tool = ToolFactory.create_or_none("nonexistent")
        assert tool is None
