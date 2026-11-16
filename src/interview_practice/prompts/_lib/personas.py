"""Private interviewer-persona instructions."""

from __future__ import annotations

from interview_practice.prompts.personas import (
    DEFAULT_PERSONA,
    PERSONA_ORDER,
    Persona,
)

_PERSONA_INSTRUCTIONS: dict[str, str] = {
    "strict": (
        "Act as a strict but fair interviewer. Be direct, probe for evidence, "
        "and do not over-praise. Ask one follow-up at a time."
    ),
    "neutral": (
        "Act as a neutral interviewer. Balance warmth with directness; ask for "
        "evidence, trade-offs and measurable outcomes."
    ),
    "friendly": (
        "Act as a friendly, encouraging interviewer. Put the candidate at ease "
        "while still asking for specific evidence and next steps."
    ),
}

_PERSONAS: dict[str, Persona] = {
    "strict": Persona(
        key="strict",
        label="Strict",
        description="Direct, evidence-heavy, minimal praise.",
    ),
    "neutral": Persona(
        key="neutral",
        label="Neutral",
        description="Balanced warmth and directness.",
    ),
    "friendly": Persona(
        key="friendly",
        label="Friendly",
        description="Encouraging, but still evidence-based.",
    ),
}


def get_persona_instruction(key: str) -> str:
    try:
        return _PERSONA_INSTRUCTIONS[key]
    except KeyError as exc:
        raise ValueError(f"Unknown interviewer persona: {key}") from exc


def persona_options() -> tuple[Persona, ...]:
    return tuple(_PERSONAS[key] for key in PERSONA_ORDER)


def get_persona(key: str) -> Persona:
    try:
        return _PERSONAS[key]
    except KeyError as exc:
        raise ValueError(f"Unknown interviewer persona: {key}") from exc


__all__ = [
    "DEFAULT_PERSONA",
    "PERSONA_ORDER",
    "Persona",
    "get_persona",
    "get_persona_instruction",
    "persona_options",
]
