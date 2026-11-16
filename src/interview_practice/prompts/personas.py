"""Public interviewer-persona records."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_PERSONA = "neutral"
PERSONA_ORDER: tuple[str, ...] = ("strict", "neutral", "friendly")


@dataclass(frozen=True, slots=True)
class Persona:
    key: str
    label: str
    description: str
