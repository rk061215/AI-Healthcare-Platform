from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from loguru import logger

from app.langgraph.graph_registry import get_global_registry
from app.langgraph.graphs.medical_qa_graph import MedicalQAGraph


@dataclass
class GraphBootstrapResult:
    graph_registered: bool = False
    graph_name: str = ""
    dependencies_validated: bool = False
    validation_errors: list[str] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    success: bool = False


class GraphBootstrap:
    @staticmethod
    def register_graphs() -> GraphBootstrapResult:
        result = GraphBootstrapResult()
        try:
            registry = get_global_registry()
            existing = registry.list_graphs()
            if "medical_qa" not in existing:
                registry.register("medical_qa", MedicalQAGraph)
                result.graph_registered = True
                result.graph_name = "medical_qa"
                result.diagnostics["registry_graphs"] = registry.list_graphs()
                logger.info("LangGraph: registered 'medical_qa' graph")
            else:
                result.graph_registered = True
                result.graph_name = "medical_qa"
                result.diagnostics["registry_graphs"] = existing
                logger.info("LangGraph: 'medical_qa' graph already registered")
        except Exception as exc:
            result.validation_errors.append(f"Graph registration failed: {exc}")
            logger.error(f"LangGraph: graph registration failed: {exc}")
        return result

    @staticmethod
    def validate_dependencies() -> GraphBootstrapResult:
        result = GraphBootstrapResult()
        errors: list[str] = []

        try:
            from app.ai import AIProviderFactory
            provider = AIProviderFactory.create(provider_name="gemini")
            provider.health_check()
            result.diagnostics["ai_provider"] = "ok"
            logger.info("LangGraph: AI provider validated")
        except Exception as exc:
            err = f"AI provider: {exc}"
            errors.append(err)
            result.diagnostics["ai_provider"] = f"error: {exc}"

        try:
            from app.rag import RAGEngine, RAGEngineConfig
            rag = RAGEngine(config=RAGEngineConfig())
            result.diagnostics["rag_engine"] = "ok"
            logger.info("LangGraph: RAG engine validated")
        except Exception as exc:
            err = f"RAG engine: {exc}"
            errors.append(err)
            result.diagnostics["rag_engine"] = f"error: {exc}"

        try:
            from app.memory.memory_service import MemoryService
            from app.memory.config import MemoryConfig
            mem = MemoryService(config=MemoryConfig(provider="in_memory"))
            result.diagnostics["memory_service"] = "ok"
            logger.info("LangGraph: memory service validated")
        except Exception as exc:
            err = f"Memory service: {exc}"
            errors.append(err)
            result.diagnostics["memory_service"] = f"error: {exc}"

        try:
            from app.tools.tool_service import ToolService
            svc = ToolService()
            tools = svc.list_tools()
            result.diagnostics["tool_service"] = f"ok ({len(tools)} tools)"
            logger.info(f"LangGraph: tool service validated ({len(tools)} tools)")
        except Exception as exc:
            err = f"Tool service: {exc}"
            errors.append(err)
            result.diagnostics["tool_service"] = f"error: {exc}"

        try:
            from app.agents.agents.medical_qa_agent import MedicalQAAgent
            agent = MedicalQAAgent()
            agent.initialize()
            result.diagnostics["medical_qa_agent"] = "ok"
            logger.info("LangGraph: MedicalQAAgent validated")
        except Exception as exc:
            err = f"MedicalQAAgent: {exc}"
            errors.append(err)
            result.diagnostics["medical_qa_agent"] = f"error: {exc}"

        try:
            from app.retrieval.retriever_service import RetrieverService
            ret = RetrieverService()
            result.diagnostics["retriever_service"] = "ok"
            logger.info("LangGraph: retriever service validated")
        except Exception as exc:
            err = f"Retriever service: {exc}"
            errors.append(err)
            result.diagnostics["retriever_service"] = f"error: {exc}"

        try:
            from app.context.context_builder import ContextBuilder
            cb = ContextBuilder()
            result.diagnostics["context_builder"] = "ok"
            logger.info("LangGraph: context builder validated")
        except Exception as exc:
            err = f"Context builder: {exc}"
            errors.append(err)
            result.diagnostics["context_builder"] = f"error: {exc}"

        try:
            from app.embeddings.embedding_service import EmbeddingService
            emb = EmbeddingService()
            result.diagnostics["embedding_service"] = "ok"
            logger.info("LangGraph: embedding service validated")
        except Exception as exc:
            err = f"Embedding service: {exc}"
            errors.append(err)
            result.diagnostics["embedding_service"] = f"error: {exc}"

        try:
            from app.vector_store.vector_service import VectorService
            vs = VectorService()
            result.diagnostics["vector_store"] = "ok"
            logger.info("LangGraph: vector store validated")
        except Exception as exc:
            err = f"Vector store: {exc}"
            errors.append(err)
            result.diagnostics["vector_store"] = f"error: {exc}"

        try:
            from app.prompts.manager import PromptManager
            pm = PromptManager()
            result.diagnostics["prompt_manager"] = "ok"
            logger.info("LangGraph: prompt manager validated")
        except Exception as exc:
            err = f"Prompt manager: {exc}"
            errors.append(err)
            result.diagnostics["prompt_manager"] = f"error: {exc}"

        result.validation_errors = errors
        result.dependencies_validated = len(errors) == 0
        return result

    @staticmethod
    def run_full_bootstrap() -> GraphBootstrapResult:
        reg_result = GraphBootstrap.register_graphs()
        dep_result = GraphBootstrap.validate_dependencies()

        combined = GraphBootstrapResult(
            graph_registered=reg_result.graph_registered,
            graph_name=reg_result.graph_name,
            dependencies_validated=dep_result.dependencies_validated,
            validation_errors=dep_result.validation_errors,
            diagnostics={**reg_result.diagnostics, **dep_result.diagnostics},
            success=reg_result.graph_registered and dep_result.dependencies_validated,
        )

        if combined.success:
            logger.info(
                "LangGraph bootstrap: OK — graph registered, "
                f"{len(combined.diagnostics)} subsystems validated"
            )
        else:
            logger.warning(
                f"LangGraph bootstrap: degraded — "
                f"{len(combined.validation_errors)} dependency issues"
            )

        return combined


_bootstrap_result: Optional[GraphBootstrapResult] = None


def get_bootstrap_result() -> Optional[GraphBootstrapResult]:
    global _bootstrap_result
    return _bootstrap_result


def set_bootstrap_result(result: GraphBootstrapResult) -> None:
    global _bootstrap_result
    _bootstrap_result = result
