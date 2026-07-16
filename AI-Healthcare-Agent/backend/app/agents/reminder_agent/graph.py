from langgraph.graph import END, StateGraph

from app.agents.reminder_agent.nodes import check_schedule, generate_reminders, track_adherence
from app.agents.reminder_agent.state import ReminderAgentState


def build_reminder_agent() -> StateGraph:
    workflow = StateGraph(ReminderAgentState)

    workflow.add_node("check_schedule", check_schedule)
    workflow.add_node("generate_reminders", generate_reminders)
    workflow.add_node("track_adherence", track_adherence)

    workflow.set_entry_point("check_schedule")
    workflow.add_edge("check_schedule", "generate_reminders")
    workflow.add_edge("generate_reminders", "track_adherence")
    workflow.add_edge("track_adherence", END)

    return workflow.compile()
