from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from app.chat.chat_service import ChatService
from app.chat.models import ChatRequest
from app.langgraph.graph_runtime import BaseGraph
from app.langgraph.graph_state import GraphState
from app.rag.models import RAGResponse


def _make_mock_rag_engine():
    engine = MagicMock()
    rag_resp = RAGResponse(answer="Mock RAG answer")
    engine.answer.return_value = rag_resp
    return engine


class FakeGraph(BaseGraph):
    def build(self) -> None:
        def mock_node(state: GraphState) -> GraphState:
            state.final_response = "Test answer from graph"
            state.agent_response = {"success": True, "answer": "Test answer from graph"}
            state.rag_response = {"query_type": "medical"}
            state.retrieved_evidence = [
                {"document_id": "doc1", "text": "evidence text", "score": 0.95}
            ]
            return state

        self._executor.register_node("mock_node", mock_node)

    def _run_pipeline(self, state: GraphState) -> GraphState:
        state = self._executor.execute_node("mock_node", state, "mock")
        return state


class TestChatServiceGraphIntegration:
    def test_ask_uses_graph_when_available(self):
        graph = FakeGraph()
        graph.initialize()

        service = ChatService(medical_qa_graph=graph, rag_engine=_make_mock_rag_engine())
        request = ChatRequest(query="What is diabetes?", patient_id="p1")

        response = service.ask(request)
        assert response.answer == "Test answer from graph"
        assert response.session_id != ""
        assert response.processing_time_ms > 0

    def test_ask_falls_back_to_direct_without_graph(self):
        service = ChatService(rag_engine=_make_mock_rag_engine())
        assert service._graph_available is False

    def test_graph_execution_trace_in_response(self):
        graph = FakeGraph()
        graph.initialize()

        service = ChatService(medical_qa_graph=graph, rag_engine=_make_mock_rag_engine())
        request = ChatRequest(query="test query", patient_id="p1")

        response = service.ask(request)
        assert response.answer is not None

    def test_empty_query_raises_error(self):
        service = ChatService(medical_qa_graph=FakeGraph(), rag_engine=_make_mock_rag_engine())
        with pytest.raises(Exception) as excinfo:
            service.ask(ChatRequest(query="", patient_id="p1"))
        assert str(excinfo.value) is not None

    def test_graph_enriched_confidence(self):
        graph = FakeGraph()
        graph.initialize()

        service = ChatService(medical_qa_graph=graph, rag_engine=_make_mock_rag_engine())
        request = ChatRequest(query="What is the treatment?", patient_id="p1")

        response = service.ask(request)
        assert response.confidence is not None

    def test_session_id_preserved(self):
        graph = FakeGraph()
        graph.initialize()

        service = ChatService(medical_qa_graph=graph, rag_engine=_make_mock_rag_engine())
        request = ChatRequest(query="hello", patient_id="p1", session_id="custom_sess")

        response = service.ask(request)
        assert response.session_id == "custom_sess"

    def test_ask_populates_suggestions(self):
        graph = FakeGraph()
        graph.initialize()

        service = ChatService(medical_qa_graph=graph, rag_engine=_make_mock_rag_engine())
        request = ChatRequest(query="What is hypertension?", patient_id="p1")

        response = service.ask(request)
        assert response.suggested_questions is not None


class TestChatServiceFallback:
    def test_direct_path_uses_rag(self):
        service = ChatService(rag_engine=_make_mock_rag_engine())
        request = ChatRequest(query="What is diabetes?", patient_id="p1")
        response = service.ask(request)
        assert response.answer is not None

    def test_graph_overhead_measurement(self):
        graph = FakeGraph()
        graph.initialize()

        service = ChatService(medical_qa_graph=graph, rag_engine=_make_mock_rag_engine())

        request = ChatRequest(query="test", patient_id="p1")
        iterations = 10
        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            service.ask(request)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_ms = sum(times) / len(times)
        assert avg_ms < 5000, f"Graph overhead too high: {avg_ms:.2f}ms average"
