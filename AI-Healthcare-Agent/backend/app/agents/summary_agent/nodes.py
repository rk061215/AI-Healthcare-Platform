from loguru import logger

from app.agents.summary_agent.state import SummaryAgentState


def aggregate_data(state: SummaryAgentState) -> SummaryAgentState:
    logger.info(f"Aggregating data for patient {state.get('patient_id')}")
    return state


def generate_summary(state: SummaryAgentState) -> SummaryAgentState:
    logger.info("Generating doctor summary")
    state["summary"] = "Patient summary will be generated in the next phase."
    return state
