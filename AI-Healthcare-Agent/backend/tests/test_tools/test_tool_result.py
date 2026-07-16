from __future__ import annotations

from app.tools.tool_result import ToolResult


class TestToolResult:
    def test_default_creation(self):
        result = ToolResult(success=True)
        assert result.success is True
        assert result.data is None
        assert result.error is None
        assert result.tool_name == ""
        assert result.action == ""
        assert result.duration_ms == 0.0
        assert result.metadata == {}

    def test_ok_factory_default(self):
        result = ToolResult.ok()
        assert result.success is True
        assert result.data is None
        assert result.error is None

    def test_ok_factory_with_data(self):
        result = ToolResult.ok(data={"key": "value"}, tool_name="test", action="act")
        assert result.success is True
        assert result.data == {"key": "value"}
        assert result.tool_name == "test"
        assert result.action == "act"

    def test_ok_factory_with_metadata(self):
        result = ToolResult.ok(metadata={"source": "test"})
        assert result.success is True
        assert result.metadata == {"source": "test"}

    def test_ok_factory_with_duration(self):
        result = ToolResult.ok(duration_ms=42.5)
        assert result.duration_ms == 42.5

    def test_error_factory_default(self):
        result = ToolResult.error_factory(error_message="something went wrong")
        assert result.success is False
        assert result.error == "something went wrong"
        assert result.data is None

    def test_error_factory_with_all_params(self):
        result = ToolResult.error_factory(
            error_message="failed",
            tool_name="appointment",
            action="book",
            duration_ms=10.0,
            metadata={"attempt": 1},
        )
        assert result.success is False
        assert result.error == "failed"
        assert result.tool_name == "appointment"
        assert result.action == "book"
        assert result.duration_ms == 10.0
        assert result.metadata == {"attempt": 1}

    def test_metadata_mutable(self):
        result = ToolResult.ok()
        result.metadata["key"] = "value"
        assert result.metadata["key"] == "value"

    def test_data_field(self):
        result = ToolResult.ok(data="string_data")
        assert result.data == "string_data"
