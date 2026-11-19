"""Provider contract shared by OpenRouter, local and demo modes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from interview_practice.messages import ChatMessage


class ProviderError(RuntimeError):
    """A provider failure that is safe to show to a user.

    Messages must never contain API keys, authorization headers or raw
    environment values.
    """


@dataclass(frozen=True, slots=True)
class CompletionRequest:
    """One non-streaming completion request at the provider seam."""

    messages: Sequence[ChatMessage]
    model: str
    temperature: float
    max_tokens: int
    top_p: float
    reasoning_effort: str | None = None
    response_format: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class Completion:
    text: str
    model: str
    provider: str
    latency_ms: int
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float | None = None
    finish_reason: str = ""
    notice: str = ""


class Provider(Protocol):
    name: str

    def list_models(self) -> list[str]:
        """Return the model IDs this provider currently exposes."""

    def complete(self, request: CompletionRequest) -> Completion:
        """Run one non-streaming completion."""
