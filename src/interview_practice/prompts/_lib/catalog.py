"""Private catalog of prompt techniques and their system layers."""

from __future__ import annotations

from dataclasses import dataclass

from interview_practice.prompts.techniques import Technique


@dataclass(frozen=True, slots=True)
class _PromptSpec:
    key: str
    label: str
    description: str
    system_layer: str


_SPECS: dict[str, _PromptSpec] = {
    "zero_shot": _PromptSpec(
        key="zero_shot",
        label="Zero-shot",
        description="A direct instruction with no examples.",
        system_layer=(
            "Use a direct zero-shot instruction. Do not add examples or ask "
            "clarifying questions; make a reasonable assumption and answer."
        ),
    ),
    "role_persona": _PromptSpec(
        key="role_persona",
        label="Role / persona",
        description="A senior hiring-manager persona sets the bar.",
        system_layer=(
            "Act as a senior AI-engineering hiring manager who has interviewed "
            "many candidates. Be specific, practical, and candid."
        ),
    ),
    "few_shot": _PromptSpec(
        key="few_shot",
        label="Few-shot",
        description="Two short examples anchor the desired shape.",
        system_layer=(
            "Use the two examples below as style guidance. Match their level of "
            "specificity, but do not copy their content.\n"
            "Example 1: A good question asks for a concrete trade-off and has "
            "three answer points.\n"
            "Example 2: A good evaluation names one strength, one gap, and one "
            "next action."
        ),
    ),
    "cot": _PromptSpec(
        key="cot",
        label="Chain-of-thought",
        description="Structured reasoning before the final artifact.",
        system_layer=(
            "Reason privately through the role requirements before you write. "
            "Do not reveal hidden chain-of-thought; put the useful rationale "
            "in the output's `why` field or in a short visible summary."
        ),
    ),
    "json_schema": _PromptSpec(
        key="json_schema",
        label="JSON schema",
        description="Schema-first output for reliable parsing.",
        system_layer=(
            "Prioritize exact schema compliance. Return one JSON object with the "
            "requested keys and no markdown fences or extra prose."
        ),
    ),
    "chained": _PromptSpec(
        key="chained",
        label="Prompt chaining",
        description="Stage one extracts requirements; stage two uses them.",
        system_layer=(
            "You are stage two of a two-stage chain. Stage one extracted the "
            "role requirements supplied in the `<Requirements>` block. Use them "
            "as constraints for this stage. Return one JSON object."
        ),
    ),
}

TECHNIQUE_ORDER: tuple[str, ...] = tuple(_SPECS)
DEFAULT_TECHNIQUE = "json_schema"


def get_spec(key: str) -> _PromptSpec:
    try:
        return _SPECS[key]
    except KeyError as exc:
        raise ValueError(f"Unknown prompt technique: {key}") from exc


def technique_options() -> tuple[Technique, ...]:
    return tuple(
        Technique(key=spec.key, label=spec.label, description=spec.description)
        for spec in _SPECS.values()
    )
