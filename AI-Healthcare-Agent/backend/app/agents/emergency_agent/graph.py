from langgraph.graph import END, StateGraph

from app.agents.emergency_agent.nodes import analyze_symptoms, classify_risk, generate_recommendations
from app.agents.emergency_agent.state import EmergencyAgentState


def build_emergency_agent() -> StateGraph:
    workflow = StateGraph(EmergencyAgentState)

    workflow.add_node("analyze_symptoms", analyze_symptoms)
    workflow.add_node("classify_risk", classify_risk)
    workflow.add_node("generate_recommendations", generate_recommendations)

    workflow.set_entry_point("analyze_symptoms")
    workflow.add_edge("analyze_symptoms", "classify_risk")
    workflow.add_edge("classify_risk", "generate_recommendations")
    workflow.add_edge("generate_recommendations", END)

    return workflow.compile()
