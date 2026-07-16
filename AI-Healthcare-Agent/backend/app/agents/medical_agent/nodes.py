from loguru import logger

from app.agents.medical_agent.state import MedicalReportState


def extract_entities(state: MedicalReportState) -> MedicalReportState:
    logger.info("Extracting medical entities from report text")
    state["raw_text"] = state.get("raw_text", "")
    if not state["raw_text"]:
        state["error"] = "No text provided for extraction"
        return state
    return state


def validate_extraction(state: MedicalReportState) -> MedicalReportState:
    logger.info("Validating extracted data")
    state["validation_status"] = "pending"
    return state


def store_results(state: MedicalReportState) -> MedicalReportState:
    logger.info("Storing extracted medical data to database")
    return state
