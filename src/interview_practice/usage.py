"""Small public summary of one model call."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CallUsage:
    """Observable metadata for one model call."""

    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float | None
    cost_source: str
    latency_ms: int
