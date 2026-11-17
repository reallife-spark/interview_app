"""Session-scoped state and process-wide budget accounting."""

from __future__ import annotations

import secrets
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import date

from interview_practice.config import Settings
from interview_practice.messages import ChatMessage
from interview_practice.prompts.schemas import AnswerEvaluation, QuestionSet
from interview_practice.usage import CallUsage


def new_canary() -> str:
    return "canary-" + secrets.token_hex(8)


@dataclass
class SessionState:
    canary: str = field(default_factory=new_canary)
    calls: int = 0
    cost_usd: float = 0.0
    messages: list[ChatMessage] = field(default_factory=list)
    questions: QuestionSet | None = None
    evaluation: AnswerEvaluation | None = None
    last_question: str = ""
    last_answer: str = ""
    last_usage: CallUsage | None = None
    usage_history: list[CallUsage] = field(default_factory=list)

    def can_call(self, settings: Settings) -> None:
        if self.calls >= settings.max_calls:
            raise RuntimeError(
                f"Session call cap reached ({settings.max_calls} calls)."
            )
        if (
            settings.session_cost_cap_usd > 0
            and self.cost_usd >= settings.session_cost_cap_usd
        ):
            raise RuntimeError(
                "Session cost cap reached. Switch to demo mode or clear the "
                "session."
            )

    def record(self, usage: CallUsage) -> None:
        self.calls += 1
        if usage.cost_usd is not None:
            self.cost_usd += usage.cost_usd
        self.last_usage = usage
        self.usage_history.append(usage)

    def reset(self) -> None:
        self.canary = new_canary()
        self.calls = 0
        self.cost_usd = 0.0
        self.messages.clear()
        self.questions = None
        self.evaluation = None
        self.last_question = ""
        self.last_answer = ""
        self.last_usage = None
        self.usage_history.clear()

    def add_message(self, role: str, content: str) -> None:
        if role not in {"system", "user", "assistant"}:
            raise ValueError(f"invalid message role: {role}")
        self.messages.append(ChatMessage(role, content))  # type: ignore[arg-type]


@dataclass
class GlobalBudget:
    """A conservative process-wide guard for a public demo.

    Streamlit Cloud may restart the process, so this is not a billing
    boundary. The OpenRouter account spend limit remains the hard stop.
    A value of zero disables that individual limit.
    """

    max_calls_per_day: int = 500
    max_cost_per_day: float = 5.0
    max_calls_per_minute: int = 30
    _day: date = field(default_factory=date.today)
    _calls: int = 0
    _cost: float = 0.0
    _recent: deque[float] = field(default_factory=deque)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def acquire(self) -> None:
        now = time.monotonic()
        with self._lock:
            self._roll_day()
            while self._recent and now - self._recent[0] >= 60.0:
                self._recent.popleft()
            if (
                self.max_calls_per_minute > 0
                and len(self._recent) >= self.max_calls_per_minute
            ):
                raise RuntimeError(
                    "Public rate limit reached; try again in a minute."
                )
            if (
                self.max_calls_per_day > 0
                and self._calls >= self.max_calls_per_day
            ):
                raise RuntimeError("Public daily call budget reached.")
            if (
                self.max_cost_per_day > 0
                and self._cost >= self.max_cost_per_day
            ):
                raise RuntimeError("Public daily cost budget reached.")
            self._calls += 1
            self._recent.append(now)

    def record(self, usage: CallUsage) -> None:
        if usage.cost_usd is None:
            return
        with self._lock:
            self._roll_day()
            self._cost += usage.cost_usd

    def snapshot(self) -> tuple[int, float]:
        with self._lock:
            self._roll_day()
            return self._calls, self._cost

    def reset(self) -> None:
        with self._lock:
            self._day = date.today()
            self._calls = 0
            self._cost = 0.0
            self._recent.clear()

    def _roll_day(self) -> None:
        today = date.today()
        if today != self._day:
            self._day = today
            self._calls = 0
            self._cost = 0.0
            self._recent.clear()
