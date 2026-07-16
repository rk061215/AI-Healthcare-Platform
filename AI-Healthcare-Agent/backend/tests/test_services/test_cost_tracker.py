from app.services.cost_tracker import CostTracker


def test_track_gpt4o_mini():
    tracker = CostTracker()
    cost = tracker.track_llm_call(
        model="gpt-4o-mini",
        agent_name="test_agent",
        input_tokens=1000,
        output_tokens=500,
    )
    expected = (1000 / 1000) * 0.0015 + (500 / 1000) * 0.006
    assert cost == round(expected, 6)


def test_track_gpt4o():
    tracker = CostTracker()
    cost = tracker.track_llm_call(
        model="gpt-4o",
        agent_name="test_agent",
        input_tokens=500,
        output_tokens=200,
    )
    expected = (500 / 1000) * 0.01 + (200 / 1000) * 0.03
    assert cost == round(expected, 6)


def test_track_unknown_model_falls_back():
    tracker = CostTracker()
    cost = tracker.track_llm_call(
        model="unknown-model",
        agent_name="test_agent",
        input_tokens=1000,
        output_tokens=1000,
    )
    expected = (1000 / 1000) * 0.0015 + (1000 / 1000) * 0.006
    assert cost == round(expected, 6)


def test_reset_daily_cost():
    tracker = CostTracker()
    tracker.track_llm_call(model="gpt-4o-mini", agent_name="test", input_tokens=100, output_tokens=50)
    assert tracker._daily_cost > 0
    tracker.reset_daily_cost()
    assert tracker._daily_cost == 0.0


def test_zero_tokens():
    tracker = CostTracker()
    cost = tracker.track_llm_call(model="gpt-4o-mini", agent_name="test", input_tokens=0, output_tokens=0)
    assert cost == 0.0


def test_accumulates_cost():
    tracker = CostTracker()
    cost1 = tracker.track_llm_call(model="gpt-4o-mini", agent_name="test", input_tokens=1000, output_tokens=0)
    cost2 = tracker.track_llm_call(model="gpt-4o-mini", agent_name="test", input_tokens=0, output_tokens=500)
    assert abs(tracker._daily_cost - round(cost1 + cost2, 6)) < 1e-10
