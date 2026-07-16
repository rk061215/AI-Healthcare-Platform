from typing import Any, Optional

from typing_extensions import TypedDict


class ChatAgentState(TypedDict):
    question: str
    patient_id: str
    context_docs: Optional[list[dict[str, Any]]]
    chat_history: Optional[list[dict[str, str]]]
    response: Optional[str]
    sources: Optional[list[dict[str, Any]]]
    error: Optional[str]
