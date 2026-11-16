"""Session-scoped state and budget accounting."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field

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
        self.last_usage = None
        self.usage_history.clear()

    def add_message(self, role: str, content: str) -> None:
        if role not in {"system", "user", "assistant"}:
            raise ValueError(f"invalid message role: {role}")
        self.messages.append(ChatMessage(role, content))  # type: ignore[arg-type]
