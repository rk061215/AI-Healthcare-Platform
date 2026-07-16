from __future__ import annotations

import pytest

from app.tools.base_tool import BaseTool
from app.tools.config import ToolConfig
from app.tools.exceptions import ToolValidationError
from app.tools.tool_context import ToolContext
from app.tools.tool_result import ToolResult
from tests.test_tools.conftest import (
    AuditingTool,
    AuthorizingTool,
    FailingTool,
    SimpleTool,
    ValidatingTool,
    VerifyingTool,
)


class TestBaseTool:
    def test_instantiation(self):
        tool = SimpleTool()
        assert tool.config is not None
        assert isinstance(tool.config, ToolConfig)

    def test_custom_config(self):
        config = ToolConfig(tool_type="custom", timeout_seconds=120)
        tool = SimpleTool(config=config)
        assert tool.config.tool_type == "custom"
        assert tool.config.timeout_seconds == 120

    def test_config_property(self):
        tool = SimpleTool()
        assert tool.config == tool._config

    def test_validate_default_passes(self, sample_context):
        tool = SimpleTool()
        tool.validate(sample_context)

    def test_validate_missing_tool_name(self):
        tool = SimpleTool()
        ctx = ToolContext(tool_name="", action="test")
        with pytest.raises(ToolValidationError, match="tool_name is required"):
            tool.validate(ctx)

    def test_validate_custom_validation(self, sample_context):
        tool = ValidatingTool()
        with pytest.raises(ToolValidationError, match="required_field is missing"):
            tool.validate(sample_context)

    def test_validate_custom_validation_passes(self, sample_context):
        tool = ValidatingTool()
        sample_context.parameters["required_field"] = "present"
        tool.validate(sample_context)

    def test_authorize_default_returns_true(self, sample_context):
        tool = SimpleTool()
        assert tool.authorize(sample_context) is True

    def test_authorize_custom(self, sample_context):
        tool = AuthorizingTool()
        assert tool.authorize(sample_context) is False
        sample_context.user_role = "admin"
        assert tool.authorize(sample_context) is True

    def test_verify_default_passthrough(self):
        tool = SimpleTool()
        result = ToolResult.ok(data={"value": 42})
        verified = tool.verify(result)
        assert verified is result

    def test_verify_custom(self):
        tool = VerifyingTool()
        result = ToolResult.ok(data={"value": "test"})
        verified = tool.verify(result)
        assert verified.metadata.get("verified") is True

    def test_audit_default_noop(self, sample_context):
        tool = SimpleTool()
        result = ToolResult.ok(data={})
        tool.audit(sample_context, result)

    def test_audit_custom(self, sample_context):
        tool = AuditingTool()
        result = ToolResult.ok(data={"audited": True})
        tool.audit(sample_context, result)
        assert len(tool.audit_log) == 1
        assert tool.audit_log[0][0] is sample_context
        assert tool.audit_log[0][1] is result

    def test_cleanup_default_noop(self, sample_context):
        tool = SimpleTool()
        tool.cleanup(sample_context)

    def test_execute(self, sample_context):
        tool = SimpleTool()
        result = tool.execute(sample_context)
        assert result.success is True
        assert result.data["message"] == "executed"

    def test_execute_failure(self, sample_context):
        tool = FailingTool()
        result = tool.execute(sample_context)
        assert result.success is False
        assert result.error == "execution failed"

    def test_abstract_class_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseTool()

    def test_can_handle_default(self):
        tool = SimpleTool()
        assert callable(getattr(tool, "execute", None))
