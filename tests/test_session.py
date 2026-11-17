from interview_practice.session import GlobalBudget, SessionState
from interview_practice.usage import CallUsage


def _usage(cost: float | None = 0.01) -> CallUsage:
    return CallUsage(
        model="demo",
        provider="demo",
        prompt_tokens=1,
        completion_tokens=1,
        total_tokens=2,
        cost_usd=cost,
        cost_source="provider",
        latency_ms=0,
    )


def test_global_call_budget_blocks_after_limit() -> None:
    budget = GlobalBudget(
        max_calls_per_day=1,
        max_cost_per_day=0,
        max_calls_per_minute=0,
    )
    budget.acquire()
    try:
        budget.acquire()
    except RuntimeError as exc:
        assert "daily call" in str(exc)
    else:
        raise AssertionError("expected budget error")


def test_global_cost_budget_blocks_after_cost() -> None:
    budget = GlobalBudget(
        max_calls_per_day=0,
        max_cost_per_day=0.01,
        max_calls_per_minute=0,
    )
    budget.acquire()
    budget.record(_usage(0.02))
    try:
        budget.acquire()
    except RuntimeError as exc:
        assert "cost" in str(exc)
    else:
        raise AssertionError("expected budget error")


def test_global_rate_limit_blocks_within_minute() -> None:
    budget = GlobalBudget(
        max_calls_per_day=0,
        max_cost_per_day=0,
        max_calls_per_minute=1,
    )
    budget.acquire()
    try:
        budget.acquire()
    except RuntimeError as exc:
        assert "rate" in str(exc)
    else:
        raise AssertionError("expected rate error")


def test_session_reset_clears_context() -> None:
    session = SessionState(last_question="q", last_answer="a")
    session.reset()
    assert session.last_question == ""
    assert session.last_answer == ""
