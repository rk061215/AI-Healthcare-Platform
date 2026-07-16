from loguru import logger

from app.agents.reminder_agent.state import ReminderAgentState


def check_schedule(state: ReminderAgentState) -> ReminderAgentState:
    logger.info(f"Checking medication schedule for patient {state.get('patient_id')}")
    return state


def generate_reminders(state: ReminderAgentState) -> ReminderAgentState:
    logger.info("Generating reminder notifications")
    return state


def track_adherence(state: ReminderAgentState) -> ReminderAgentState:
    logger.info("Tracking medication adherence")
    return state
