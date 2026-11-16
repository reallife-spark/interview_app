"""Private prompt templates and message builders."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape
from textwrap import dedent

from interview_practice.messages import ChatMessage
from interview_practice.prompts._lib.catalog import get_spec
from interview_practice.prompts._lib.defensive import defensive_system_prompt

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


def _job_description_block(value: str) -> str:
    return f"<JobDescription>{escape(value.strip() or 'Not provided')}</JobDescription>"


def build_system_prompt(technique: str, canary: str) -> str:
    selected = get_spec(technique)
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
    selected = get_spec(technique)
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
    selected = get_spec(technique)
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
    selected = get_spec(technique)
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
