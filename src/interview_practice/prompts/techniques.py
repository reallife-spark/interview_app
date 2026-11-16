"""Public prompt-technique records."""

from __future__ import annotations

from dataclasses import dataclass

PROMPT_VERSION = "2026-11-16"


@dataclass(frozen=True, slots=True)
class Technique:
    key: str
    label: str
    description: str
