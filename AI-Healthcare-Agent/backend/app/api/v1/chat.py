from typing import Optional, Tuple

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_patient, get_db
from app.database.enums import ReportStatus
from app.models.report import Report
from app.schemas.chat import ChatMessageRequest, ChatResponse
from app.services.chat_service import ChatService as DbChatService
from app.chat.chat_service import ChatService as GraphChatService


router = APIRouter()


def _get_graph():
    return None


def _get_patient_report_text(db: Session, patient_id: str) -> Tuple[Optional[str], Optional[str]]:
    report = (
        db.query(Report)
        .filter(Report.patient_id == patient_id, Report.status == ReportStatus.COMPLETED, Report.ocr_text.isnot(None))
        .order_by(Report.processed_at.desc())
        .first()
    )
    if report:
        return str(report.id), report.ocr_text
    return None, None


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

    try:
        graph = _get_graph()
        graph_chat = GraphChatService(medical_qa_graph=graph)

        chat_request = ChatMessageRequestToChatRequest(request, payload["sub"])
        report_id, report_text = _get_patient_report_text(db, payload["sub"])
        if report_id and not chat_request.report_id:
            chat_request.report_id = report_id

        result = graph_chat.ask(chat_request, document_text=report_text)

        return ChatResponse(
            reply=result.answer,
            sources=result.citations if hasattr(result, "citations") else None,
            suggested_questions=[q.question for q in result.suggested_questions] if hasattr(result, "suggested_questions") and result.suggested_questions else None,
            metadata={
                "session_id": result.session_id,
                "confidence": result.confidence.overall if hasattr(result, "confidence") else 0.0,
                "query_type": result.query_type if hasattr(result, "query_type") else "unknown",
                "processing_time_ms": result.processing_time_ms if hasattr(result, "processing_time_ms") else 0.0,
            },
        )
    except Exception as exc:
        return ChatResponse(
            reply=f"AI service is not available. Please verify the GEMINI_API_KEY is set correctly on the server. Details: {exc}",
            metadata={
                "error": str(exc),
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
