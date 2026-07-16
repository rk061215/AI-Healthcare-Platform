from __future__ import annotations

from app.langgraph.graph_state import GraphState
from app.langgraph.nodes import (
    context_builder_node,
    load_memory_node,
    response_generator_node,
    tool_selector_node,
)


class TestLoadMemoryNode:
    def test_no_memory_service_available(self):
        state = GraphState(session_id="sess_1", query="hello")
        result = load_memory_node(state)
        assert len(result.memory_entries) == 0
        assert any("no memory_service" in u for u in result.context_updates)

    def test_no_session_id(self):
        state = GraphState(query="hello")
        result = load_memory_node(state)
        assert len(result.memory_entries) == 0


class TestToolSelectorNode:
    def test_tool_keyword_detected(self):
        state = GraphState(query="schedule an appointment for tomorrow")
        result = tool_selector_node(state)
        assert result.need_tool is True
        assert "schedule" in result.tool_decision["matched_keywords"]
        assert result.tool_decision["needs_tool"] is True

    def test_no_tool_keyword(self):
        state = GraphState(query="what is diabetes")
        result = tool_selector_node(state)
        assert result.need_tool is False
        assert result.tool_decision["needs_tool"] is False

    def test_empty_query(self):
        state = GraphState(query="")
        result = tool_selector_node(state)
        assert result.need_tool is False

    def test_case_insensitive_matching(self):
        state = GraphState(query="REMIND me about my medication")
        result = tool_selector_node(state)
        assert result.need_tool is True


class TestContextBuilderNode:
    def test_no_retrieved_evidence(self):
        state = GraphState(query="test", retrieved_evidence=[])
        result = context_builder_node(state)
        assert result.built_context == ""

    def test_no_context_builder_service(self):
        state = GraphState(
            query="test",
            retrieved_evidence=[{"document_id": "doc1", "text": "sample", "score": 0.9}],
        )
        result = context_builder_node(state)
        assert any("no context_builder" in u for u in result.context_updates)


class TestResponseGeneratorNode:
    def test_agent_answer_used_when_available(self):
        state = GraphState(
            query="test",
            agent_response={"success": True, "answer": "agent answer"},
        )
        result = response_generator_node(state)
        assert result.final_response == "agent answer"
        assert result.response_metadata["source"] == "agent"

    def test_rag_answer_used_as_fallback(self):
        state = GraphState(
            query="test",
            agent_response={"success": False, "answer": ""},
            rag_response={"answer": "rag answer"},
        )
        result = response_generator_node(state)
        assert result.final_response == "rag answer"
        assert result.response_metadata["source"] == "rag"

    def test_tool_result_used(self):
        state = GraphState(
            query="test",
            agent_response={"success": False, "answer": ""},
            rag_response={"answer": ""},
            tool_result={"success": True, "data": "tool data"},
        )
        result = response_generator_node(state)
        assert result.final_response == "tool data"
        assert result.response_metadata["source"] == "tool"

    def test_fallback_response_when_nothing_available(self):
        state = GraphState(
            query="test",
            agent_response={"success": False, "answer": ""},
            rag_response={},
            tool_result={},
        )
        result = response_generator_node(state)
        assert "unable to process" in result.final_response
        assert result.response_metadata["source"] == "fallback"
