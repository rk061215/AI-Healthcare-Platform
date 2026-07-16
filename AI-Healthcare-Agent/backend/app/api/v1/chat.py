from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_patient, get_db
from app.schemas.chat import ChatMessageRequest, ChatResponse
from app.services.chat_service import ChatService as DbChatService
from app.chat.chat_service import ChatService as GraphChatService
from app.langgraph.graph_registry import get_global_registry
from app.langgraph.graphs.medical_qa_graph import MedicalQAGraph

router = APIRouter()

_graph_instance: MedicalQAGraph | None = None


def _get_graph() -> MedicalQAGraph | None:
    global _graph_instance
    if _graph_instance is None:
        try:
            registry = get_global_registry()
            graph_cls = registry.get("medical_qa")
            _graph_instance = graph_cls()
            _graph_instance.initialize()
        except Exception:
            _graph_instance = None
    return _graph_instance


@router.post("/message", response_model=ChatResponse)
def send_message(
    request: ChatMessageRequest,
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    db_chat_service = DbChatService(db)
    db_chat_service.save_message(
        patient_id=payload["sub"],
        role="user",
        message=request.message,
    )

    graph = _get_graph()
    graph_chat = GraphChatService(medical_qa_graph=graph)
    result = graph_chat.ask(
        ChatMessageRequestToChatRequest(request, payload["sub"])
    )

    return ChatResponse(
        reply=result.answer,
        sources=result.citations if hasattr(result, "citations") else None,
        metadata={
            "session_id": result.session_id,
            "confidence": result.confidence.overall if hasattr(result, "confidence") else 0.0,
            "query_type": result.query_type if hasattr(result, "query_type") else "unknown",
            "processing_time_ms": result.processing_time_ms if hasattr(result, "processing_time_ms") else 0.0,
            "graph_executed": graph is not None,
        },
    )


@router.get("/history")
def get_chat_history(
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = DbChatService(db)
    messages = service.get_history(payload["sub"])
    return [
        {
            "id": str(m.id),
            "role": m.role,
            "message": m.message,
            "metadata": m.metadata_,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.delete("/history")
def clear_chat_history(
    payload: dict = Depends(get_current_patient),
    db: Session = Depends(get_db),
):
    service = DbChatService(db)
    service.clear_history(payload["sub"])
    return {"message": "Chat history cleared"}


def ChatMessageRequestToChatRequest(req: ChatMessageRequest, patient_id: str):
    from app.chat.models import ChatRequest
    return ChatRequest(
        query=req.message,
        patient_id=patient_id,
        session_id=None,
        report_id=None,
        document_type=None,
    )
