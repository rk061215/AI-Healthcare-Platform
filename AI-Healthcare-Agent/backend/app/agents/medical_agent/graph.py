from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.medical_agent.nodes import extract_entities, store_results, validate_extraction
from app.agents.medical_agent.state import MedicalReportState


def build_medical_report_agent() -> StateGraph:
    workflow = StateGraph(MedicalReportState)

    workflow.add_node("extract_entities", extract_entities)
    workflow.add_node("validate_extraction", validate_extraction)
    workflow.add_node("store_results", store_results)

    workflow.set_entry_point("extract_entities")

    workflow.add_conditional_edges(
        "extract_entities",
        lambda state: "validate_extraction" if state.get("raw_text") else END,
    )
    workflow.add_conditional_edges(
        "validate_extraction",
        lambda state: "store_results" if state.get("extracted_data") else END,
    )
    workflow.add_edge("store_results", END)

    return workflow.compile()
