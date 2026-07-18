from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.langgraph.bootstrap import get_bootstrap_result
from app.langgraph.graph_registry import get_global_registry
from app.langgraph.graphs.medical_qa_graph import MedicalQAGraph
from app.vector_recovery.recovery_manager import RecoveryManager

router = APIRouter()


@router.get("/ready")
def readiness_probe(db: Session = Depends(get_db)):
    checks: dict[str, str] = {}
    unready: list[str] = []

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "pass"
    except Exception:
        checks["database"] = "fail"
        unready.append("database")

    try:
        result = db.execute(
            text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1")
        )
        if result.fetchone():
            checks["migrations"] = "pass"
        else:
            checks["migrations"] = "fail"
            unready.append("migrations")
    except Exception:
        checks["migrations"] = "fail"
        unready.append("migrations")

    try:
        registry = get_global_registry()
        graph_list = registry.list_graphs()
        if "medical_qa" in graph_list:
            checks["graph_registry"] = "pass"
        else:
            checks["graph_registry"] = "fail"
            unready.append("graph_registry")
    except Exception:
        checks["graph_registry"] = "fail"
        unready.append("graph_registry")

    try:
        from app.tools.tool_registry import get_global_registry as get_tool_registry
        tool_list = get_tool_registry().list_tools()
        checks["tool_registry"] = f"pass ({len(tool_list)} tools)"
    except Exception:
        checks["tool_registry"] = "fail"
        unready.append("tool_registry")

    try:
        from app.memory.memory_service import MemoryService
        from app.memory.config import MemoryConfig
        ms = MemoryService(config=MemoryConfig(provider="in_memory"))
        _ = ms.list_sessions()
        checks["memory_framework"] = "pass"
    except Exception:
        checks["memory_framework"] = "fail"
        unready.append("memory_framework")

    try:
        from app.ai import AIProviderFactory
        provider = AIProviderFactory.create(provider_name="gemini")
        hc = provider.health_check()
        checks["ai_provider"] = "pass" if hc.get("status") == "ok" else "fail"
        if checks["ai_provider"] == "fail":
            unready.append("ai_provider")
    except Exception:
        checks["ai_provider"] = "fail"
        unready.append("ai_provider")

    try:
        from app.embeddings.embedding_service import EmbeddingService
        es = EmbeddingService()
        _ = es.health_check()
        checks["embedding_provider"] = "pass"
    except Exception:
        checks["embedding_provider"] = "fail"
        unready.append("embedding_provider")

    try:
        from app.vector_store.vector_service import VectorService
        vs = VectorService()
        _ = vs.health_check()
        checks["vector_store"] = "pass"
    except Exception:
        checks["vector_store"] = "fail"
        unready.append("vector_store")

    try:
        from app.retrieval.retriever_service import RetrieverService
        rs = RetrieverService()
        _ = rs.health_check()
        checks["retriever"] = "pass"
    except Exception:
        checks["retriever"] = "fail"
        unready.append("retriever")

    try:
        from app.prompts.manager import PromptManager
        pm = PromptManager()
        _ = pm.list_prompts()
        checks["prompt_manager"] = "pass"
    except Exception:
        checks["prompt_manager"] = "fail"
        unready.append("prompt_manager")

    try:
        mgr = RecoveryManager()
        vh = mgr.check_health()
        if vh.status == "healthy":
            checks["vector_recovery"] = f"pass ({vh.indexed_reports} indexed)"
        elif vh.status == "rebuilding":
            checks["vector_recovery"] = f"rebuilding ({vh.actual_document_count}/{vh.indexed_reports} indexed)"
            unready.append("vector_recovery")
        elif vh.status == "degraded":
            checks["vector_recovery"] = f"degraded ({vh.pending_rebuild_count} pending, {vh.failed_rebuild_count} failed)"
            if vh.pending_rebuild_count > 0 or not vh.collection_exists:
                unready.append("vector_recovery")
        else:
            checks["vector_recovery"] = "fail"
            unready.append("vector_recovery")
    except Exception as exc:
        checks["vector_recovery"] = "fail"
        unready.append("vector_recovery")

    bootstrap = get_bootstrap_result()
    if bootstrap:
        checks["graph_bootstrap"] = "pass" if bootstrap.success else "degraded"
        if not bootstrap.success:
            unready.append("graph_bootstrap")

    is_ready = len(unready) == 0

    return {
        "status": "ready" if is_ready else "not_ready",
        "checks": checks,
        "unready_services": unready,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
