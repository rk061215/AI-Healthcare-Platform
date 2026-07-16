from loguru import logger

from app.agents.emergency_agent.state import EmergencyAgentState


def analyze_symptoms(state: EmergencyAgentState) -> EmergencyAgentState:
    logger.info("Analyzing patient symptoms")
    return state


def classify_risk(state: EmergencyAgentState) -> EmergencyAgentState:
    logger.info("Classifying risk level")
    state["risk_level"] = "LOW"
    return state


def generate_recommendations(state: EmergencyAgentState) -> EmergencyAgentState:
    logger.info("Generating recommendations")
    state["recommendations"] = ["Consult your doctor if symptoms persist."]
    state["disclaimer"] = "This is not a medical diagnosis. Always consult a healthcare professional."
    return state
