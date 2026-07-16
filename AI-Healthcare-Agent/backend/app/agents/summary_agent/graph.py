from langgraph.graph import END, StateGraph

from app.agents.summary_agent.nodes import aggregate_data, generate_summary
from app.agents.summary_agent.state import SummaryAgentState


def build_summary_agent() -> StateGraph:
    workflow = StateGraph(SummaryAgentState)

    workflow.add_node("aggregate_data", aggregate_data)
    workflow.add_node("generate_summary", generate_summary)

    workflow.set_entry_point("aggregate_data")
    workflow.add_edge("aggregate_data", "generate_summary")
    workflow.add_edge("generate_summary", END)

    return workflow.compile()
