from langgraph.graph import END, StateGraph

from app.agents.chat_agent.nodes import generate_response, retrieve_context
from app.agents.chat_agent.state import ChatAgentState


def build_patient_chat_agent() -> StateGraph:
    workflow = StateGraph(ChatAgentState)

    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("generate_response", generate_response)

    workflow.set_entry_point("retrieve_context")
    workflow.add_edge("retrieve_context", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow.compile()
