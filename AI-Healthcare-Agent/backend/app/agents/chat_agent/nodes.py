from loguru import logger

from app.agents.chat_agent.state import ChatAgentState


def retrieve_context(state: ChatAgentState) -> ChatAgentState:
    logger.info(f"Retrieving context for patient {state.get('patient_id')}")
    return state


def generate_response(state: ChatAgentState) -> ChatAgentState:
    logger.info("Generating response using LLM")
    state["response"] = "AI chat response will be generated in the next phase."
    return state
