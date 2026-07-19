from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ChatMessageRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: str
    patient_id: str
    role: str
    message: str
    metadata: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatResponse(BaseModel):
    reply: str
    sources: Optional[list[dict]] = None
    suggested_questions: Optional[list[str]] = None
    metadata: Optional[dict] = None


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
    total: int
