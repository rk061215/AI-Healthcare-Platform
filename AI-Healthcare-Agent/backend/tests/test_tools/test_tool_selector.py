from __future__ import annotations

import re

import pytest

from app.tools.exceptions import ToolSelectorError
from app.tools.tool_selector import ToolSelector, TOOL_RULES


class TestToolSelector:
    def test_default_rules(self):
        selector = ToolSelector()
        assert len(selector._rules) == len(TOOL_RULES)

    def test_select_appointment_book(self):
        selector = ToolSelector()
        tool, action = selector.select("I want to book an appointment with Dr. Smith")
        assert tool == "appointment"
        assert action == "book"

    def test_select_appointment_cancel(self):
        selector = ToolSelector()
        tool, action = selector.select("cancel my appointment")
        assert tool == "appointment"
        assert action == "cancel"

    def test_select_appointment_reschedule(self):
        selector = ToolSelector()
        tool, action = selector.select("reschedule my appointment")
        assert tool == "appointment"
        assert action == "reschedule"

    def test_select_appointment_list(self):
        selector = ToolSelector()
        tool, action = selector.select("show my upcoming appointments")
        assert tool == "appointment"
        assert action == "list"

    def test_select_doctor(self):
        selector = ToolSelector()
        tool, action = selector.select("who is my doctor")
        assert tool == "doctor"
        assert action == "assigned_doctor"

    def test_select_doctor_specialization(self):
        selector = ToolSelector()
        tool, action = selector.select("what is my doctor's specialization")
        assert tool == "doctor"
        assert action == "specialization"

    def test_select_doctor_availability(self):
        selector = ToolSelector()
        tool, action = selector.select("doctor availability")
        assert tool == "doctor"
        assert action == "availability"

    def test_select_report_list(self):
        selector = ToolSelector()
        tool, action = selector.select("list my reports")
        assert tool == "report"
        assert action == "list"

    def test_select_report_summarize(self):
        selector = ToolSelector()
        tool, action = selector.select("summarize my report")
        assert tool == "report"
        assert action == "summarize"

    def test_select_report_metadata(self):
        selector = ToolSelector()
        tool, action = selector.select("report metadata")
        assert tool == "report"
        assert action == "metadata"

    def test_select_patient_profile(self):
        selector = ToolSelector()
        tool, action = selector.select("get my patient profile")
        assert tool == "patient"
        assert action == "get_profile"

    def test_select_patient_active_reports(self):
        selector = ToolSelector()
        tool, action = selector.select("show my active reports")
        assert tool == "patient"
        assert action == "active_reports"

    def test_select_medication_schedule(self):
        selector = ToolSelector()
        tool, action = selector.select("what medicines am I taking")
        assert tool == "medication"
        assert action == "schedule"

    def test_select_medication_explain(self):
        selector = ToolSelector()
        tool, action = selector.select("explain this medication")
        assert tool == "medication"
        assert action == "explain"

    def test_select_no_match_raises(self):
        selector = ToolSelector()
        with pytest.raises(ToolSelectorError, match="No tool matched"):
            selector.select("what is the weather today")

    def test_select_or_none_known(self):
        selector = ToolSelector()
        result = selector.select_or_none("book appointment")
        assert result is not None
        assert result[0] == "appointment"

    def test_select_or_none_unknown(self):
        selector = ToolSelector()
        result = selector.select_or_none("what is the weather")
        assert result is None

    def test_custom_rules(self):
        custom_rules = [
            (re.compile(r"weather", re.IGNORECASE), "weather", "forecast"),
        ]
        selector = ToolSelector(rules=custom_rules)
        tool, action = selector.select("what is the weather today")
        assert tool == "weather"
        assert action == "forecast"

    def test_case_insensitive(self):
        selector = ToolSelector()
        tool, action = selector.select("BOOK APPOINTMENT NOW")
        assert tool == "appointment"

    def test_medication_fallback(self):
        selector = ToolSelector()
        tool, action = selector.select("my prescription")
        assert tool == "medication"
        assert action == "schedule"
