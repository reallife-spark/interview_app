"""Six prompt variants and the message builders used by the app."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from html import escape
from textwrap import dedent

from interview_practice.prompts.defensive import defensive_system_prompt
from interview_practice.providers.base import ChatMessage


@dataclass(frozen=True, slots=True)
class Technique:
    key: str
    label: str
    description: str
    system_layer: str


TECHNIQUES: dict[str, Technique] = {
    "zero_shot": Technique(
        key="zero_shot",
        label="Zero-shot",
        description="A direct instruction with no examples.",
        system_layer=(
            "Use a direct zero-shot instruction. Do not add examples or ask "
            "clarifying questions; make a reasonable assumption and answer."
        ),
    ),
    "role_persona": Technique(
        key="role_persona",
        label="Role / persona",
        description="A senior hiring-manager persona sets the bar.",
        system_layer=(
            "Act as a senior AI-engineering hiring manager who has interviewed "
            "many candidates. Be specific, practical, and candid."
        ),
    ),
    "few_shot": Technique(
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
    "cot": Technique(
        key="cot",
        label="Chain-of-thought",
        description="Structured reasoning before the final artifact.",
        system_layer=(
            "Reason privately through the role requirements before you write. "
            "Do not reveal hidden chain-of-thought; put the useful rationale "
            "in the output's `why` field or in a short visible summary."
        ),
    ),
    "json_schema": Technique(
        key="json_schema",
        label="JSON schema",
        description="Schema-first output for reliable parsing.",
        system_layer=(
            "Prioritize exact schema compliance. Return one JSON object with the "
            "requested keys and no markdown fences or extra prose."
        ),
    ),
    "chained": Technique(
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

TECHNIQUE_ORDER: tuple[str, ...] = tuple(TECHNIQUES)
DEFAULT_TECHNIQUE = "json_schema"

QUESTION_SET_SCHEMA_HINT = """{
  "role": "string",
  "questions": [
    {
      "id": "q1",
      "category": "technical | behavioural | system-design | role-specific | closing",
      "difficulty": "easy | medium | hard",
      "question": "string",
      "why": "string",
      "answer_points": ["string", "string"]
    }
  ]
}"""

ANSWER_EVALUATION_SCHEMA_HINT = """{
  "score": 0,
  "summary": "string",
  "strengths": ["string"],
  "gaps": ["string"],
  "improved_answer": "string",
  "next_steps": ["string"]
}"""


def get_technique(key: str) -> Technique:
    try:
        return TECHNIQUES[key]
    except KeyError as exc:
        raise ValueError(f"Unknown prompt technique: {key}") from exc


def _job_description_block(value: str) -> str:
    return f"<JobDescription>{escape(value.strip() or 'Not provided')}</JobDescription>"


def build_system_prompt(technique: str, canary: str) -> str:
    selected = get_technique(technique)
    return (
        defensive_system_prompt(canary)
        + "\n\nPrompt technique: "
        + selected.label
        + "\n"
        + selected.system_layer
    )


def question_set_messages(
    technique: str,
    *,
    role: str,
    job_description: str,
    difficulty: str,
    count: int,
    canary: str,
    requirements: str = "",
) -> list[ChatMessage]:
    selected = get_technique(technique)
    user = dedent(
        f"""
        <Task>Generate {count} interview questions.</Task>
        <Role>{escape(role.strip() or "AI engineer")}</Role>
        <Difficulty>{escape(difficulty.strip() or "medium")}</Difficulty>
        {_job_description_block(job_description)}
        <Requirements>{escape(requirements.strip() or "Not provided")}</Requirements>

        Make the questions specific to the role and, when a job description is
        provided, to its actual requirements. Use a mix of categories and the
        requested difficulty. Return only JSON matching this shape:
        {QUESTION_SET_SCHEMA_HINT}
        """
    ).strip()
    return [
        ChatMessage("system", build_system_prompt(selected.key, canary)),
        ChatMessage("user", user),
    ]


def chain_stage_one_messages(
    *,
    role: str,
    job_description: str,
    canary: str,
) -> list[ChatMessage]:
    """Stage one of the chained technique: extract requirements as plain text."""

    user = dedent(
        f"""
        <Task>Extract the key interview requirements for this role.</Task>
        <Role>{escape(role.strip() or "AI engineer")}</Role>
        {_job_description_block(job_description)}

        Return 5 to 8 concise bullets covering technical skills, seniority,
        collaboration, and likely interview themes. Do not write questions yet.
        """
    ).strip()
    system = build_system_prompt("role_persona", canary) + (
        "\nYou are stage one of a two-stage chain. Return plain text bullets."
    )
    return [
        ChatMessage("system", system),
        ChatMessage("user", user),
    ]


def answer_evaluation_messages(
    technique: str,
    *,
    question: str,
    answer: str,
    job_description: str,
    canary: str,
) -> list[ChatMessage]:
    selected = get_technique(technique)
    user = dedent(
        f"""
        <Task>Evaluate this interview answer.</Task>
        <Question>{escape(question.strip() or "Not provided")}</Question>
        <Answer>{escape(answer.strip() or "Not provided")}</Answer>
        {_job_description_block(job_description)}

        Score the answer against the question and the role. Be specific and
        constructive. Return only JSON matching this shape:
        {ANSWER_EVALUATION_SCHEMA_HINT}
        """
    ).strip()
    return [
        ChatMessage("system", build_system_prompt(selected.key, canary)),
        ChatMessage("user", user),
    ]


def chat_messages(
    technique: str,
    *,
    history: Sequence[ChatMessage],
    user_message: str,
    job_description: str,
    canary: str,
) -> list[ChatMessage]:
    selected = get_technique(technique)
    messages = [ChatMessage("system", build_system_prompt(selected.key, canary))]
    messages.extend(history)
    content = user_message.strip()
    if job_description.strip() and not history:
        content = (
            f"<JobDescription>{escape(job_description.strip())}</JobDescription>\n\n"
            + content
        )
    messages.append(ChatMessage("user", content))
    return messages
