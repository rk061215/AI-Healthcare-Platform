from app.services.llm_analytics import LLMAnalyticsTracker


def test_record_and_report():
    tracker = LLMAnalyticsTracker()
    tracker.record_llm_call(
        agent_name="chat_agent",
        model="gpt-4o",
        latency_ms=1500,
        input_tokens=500,
        output_tokens=200,
        prompt_path="chat/patient_chat",
        success=True,
    )
    report = tracker.get_report("chat_agent")
    assert report.agent_name == "chat_agent"
    assert report.calls == 1
    assert "gpt-4o" in report.models
    assert report.models["gpt-4o"]["tokens_in"] == 500
    assert report.models["gpt-4o"]["tokens_out"] == 200


def test_record_error():
    tracker = LLMAnalyticsTracker()
    tracker.record_llm_call(
        agent_name="chat_agent",
        model="gpt-4o",
        latency_ms=3000,
        input_tokens=100,
        output_tokens=0,
        prompt_path="chat/patient_chat",
        success=False,
        error_type="timeout",
    )
    report = tracker.get_report("chat_agent")
    assert report.errors.get("timeout") == 1


def test_record_fallback():
    tracker = LLMAnalyticsTracker()
    tracker.record_fallback("chat_agent", "gpt-4o", "gpt-4o-mini")
    report = tracker.get_report("chat_agent")
    assert "gpt-4o→gpt-4o-mini" in report.fallbacks
    assert report.fallbacks["gpt-4o→gpt-4o-mini"] == 1


def test_record_guardrail_block():
    tracker = LLMAnalyticsTracker()
    tracker.record_guardrail_block("chat_agent")
    report = tracker.get_report("chat_agent")
    assert report.guardrail_block_rate > 0


def test_record_human_review():
    tracker = LLMAnalyticsTracker()
    tracker.record_human_review("chat_agent")
    report = tracker.get_report("chat_agent")
    assert report.human_review_rate > 0


def test_multi_calls_latency():
    tracker = LLMAnalyticsTracker()
    for i in range(10):
        tracker.record_llm_call(
            agent_name="chat_agent",
            model="gpt-4o-mini",
            latency_ms=float(i * 100),
            input_tokens=100,
            output_tokens=50,
            prompt_path="chat/test",
            success=True,
        )
    report = tracker.get_report("chat_agent")
    assert report.calls == 10
    assert report.avg_latency_ms == 450.0
    assert report.p95_latency_ms == 900.0


def test_empty_report():
    tracker = LLMAnalyticsTracker()
    report = tracker.get_report("nonexistent")
    assert report.calls == 0
    assert report.models == {}
    assert report.errors == {}
