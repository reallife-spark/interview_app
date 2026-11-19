"""Private prompt templates and message builders."""

from __future__ import annotations

from collections.abc import Sequence
from html import escape
from textwrap import dedent

from interview_practice.messages import ChatMessage
from interview_practice.prompts._lib.catalog import get_spec
from interview_practice.prompts._lib.defensive import defensive_system_prompt
from interview_practice.prompts._lib.personas import (
    DEFAULT_PERSONA,
    get_persona,
    get_persona_instruction,
)
from interview_practice.prompts.domains import DEFAULT_DOMAIN, get_domain
from interview_practice.prompts.styles import DEFAULT_STYLE, get_style

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
  "score": 85,
  "summary": "string",
  "strengths": ["string"],
  "gaps": ["string"],
  "improved_answer": "string",
  "next_steps": ["string"]
}"""

JUDGE_SCHEMA_HINT = """{
  "score": 0,
  "verdict": "string",
  "criteria": [
    {"name": "string", "score": 0, "rationale": "string"}
  ],
  "rationale": "string"
}"""

RUBRIC_SCHEMA_HINT = """{
  "role": "string",
  "criteria": [
    {
      "key": "technical_depth",
      "label": "Technical depth",
      "weight": 30,
      "descriptors": ["what a strong answer shows", "what a weak answer misses"]
    },
    {
      "key": "problem_solving",
      "label": "Problem solving",
      "weight": 25,
      "descriptors": [
        "how the candidate diagnoses",
        "how the candidate chooses a trade-off"
      ]
    },
    {
      "key": "communication",
      "label": "Communication",
      "weight": 25,
      "descriptors": ["structure and clarity", "checks understanding"]
    },
    {
      "key": "role_fit",
      "label": "Role fit",
      "weight": 20,
      "descriptors": ["relevant examples", "motivation and ownership"]
    }
  ]
}"""


def _job_description_block(value: str) -> str:
    return f"<JobDescription>{escape(value.strip() or 'Not provided')}</JobDescription>"


def budget_messages(
    messages: list[ChatMessage],
    max_tokens: int,
) -> list[ChatMessage]:
    """Add a concise output-budget note to the last user message."""

    if max_tokens <= 0 or not messages:
        return messages
    hint = (
        f"\n\nBudget: the application will stop the response at about "
        f"{max_tokens} completion tokens. Keep the response complete and "
        "concise. If it is JSON, keep the whole object valid; use short field "
        "values and at most two answer points when space is tight. Do not add "
        "commentary."
    )
    last = messages[-1]
    return [*messages[:-1], ChatMessage(last.role, last.content + hint)]


def build_system_prompt(
    technique: str,
    canary: str,
    *,
    domain: str = DEFAULT_DOMAIN,
    style: str = DEFAULT_STYLE,
) -> str:
    selected = get_spec(technique)
    selected_domain = get_domain(domain)
    selected_style = get_style(style)
    return (
        defensive_system_prompt(canary)
        + "\n\nPrompt technique: "
        + selected.label
        + "\n"
        + selected.system_layer
        + "\n\nDomain: "
        + selected_domain.label
        + ". "
        + selected_domain.instruction
        + "\nResponse style: "
        + selected_style.label
        + ". "
        + selected_style.instruction
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
    domain: str = DEFAULT_DOMAIN,
    style: str = DEFAULT_STYLE,
) -> list[ChatMessage]:
    selected = get_spec(technique)
    selected_domain = get_domain(domain)
    user = dedent(
        f"""
        <Task>Generate {count} interview questions.</Task>
        <Role>{escape(role.strip() or "AI engineer")}</Role>
        <Domain>{escape(selected_domain.label)}</Domain>
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
        ChatMessage(
            "system",
            build_system_prompt(selected.key, canary, domain=domain, style=style),
        ),
        ChatMessage("user", user),
    ]


def chain_stage_one_messages(
    *,
    role: str,
    job_description: str,
    canary: str,
    domain: str = DEFAULT_DOMAIN,
    style: str = DEFAULT_STYLE,
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
    system = build_system_prompt(
        "role_persona", canary, domain=domain, style=style
    ) + ("\nYou are stage one of a two-stage chain. Return plain text bullets.")
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
    domain: str = DEFAULT_DOMAIN,
    style: str = DEFAULT_STYLE,
) -> list[ChatMessage]:
    selected = get_spec(technique)
    user = dedent(
        f"""
        <Task>Evaluate this interview answer.</Task>
        <Question>{escape(question.strip() or "Not provided")}</Question>
        <Answer>{escape(answer.strip() or "Not provided")}</Answer>
        {_job_description_block(job_description)}

        Score the answer against the question and the role. Be specific and
        constructive. `score` must be an integer from 0 to 100 (0 = poor,
        100 = excellent), not a string, a decimal, or a 0-10 / 1-5 scale.
        `strengths`, `gaps` and `next_steps` are lists of short strings and may
        be empty. Return one JSON object with exactly these keys,
        no markdown fences and no extra prose:
        {ANSWER_EVALUATION_SCHEMA_HINT}
        """
    ).strip()
    return [
        ChatMessage(
            "system",
            build_system_prompt(selected.key, canary, domain=domain, style=style),
        ),
        ChatMessage("user", user),
    ]


def rubric_messages(
    *,
    role: str,
    job_description: str,
    canary: str,
    domain: str = DEFAULT_DOMAIN,
    style: str = DEFAULT_STYLE,
) -> list[ChatMessage]:
    user = dedent(
        f"""
        <Task>Create structured interviewer guidelines for this role.</Task>
        <Role>{escape(role.strip() or "AI engineer")}</Role>
        {_job_description_block(job_description)}

        Produce 4 to 6 criteria. Use only these keys: technical_depth,
        problem_solving, communication, role_fit, collaboration, ownership.
        Each criterion needs a label, an integer weight from 1 to 100, and at
        least two descriptors. The weights must total exactly 100. Repeat the
        role exactly in the "role" field. Adapt the labels and descriptors to
        the role; do not copy the example text. Return only one JSON object
        matching this shape, with no markdown fences or commentary:
        {RUBRIC_SCHEMA_HINT}
        """
    ).strip()
    return [
        ChatMessage(
            "system",
            build_system_prompt("json_schema", canary, domain=domain, style=style),
        ),
        ChatMessage("user", user),
    ]


def judge_messages(
    *,
    question: str,
    answer: str,
    evaluation_json: str,
    canary: str,
    domain: str = DEFAULT_DOMAIN,
    style: str = DEFAULT_STYLE,
) -> list[ChatMessage]:
    user = dedent(
        f"""
        <Task>Judge this interview answer independently.</Task>
        <Question>{escape(question.strip() or "Not provided")}</Question>
        <Answer>{escape(answer.strip() or "Not provided")}</Answer>
        <FirstPassEvaluation>
        {escape(evaluation_json or "Not provided")}
        </FirstPassEvaluation>

        Score correctness, structure, evidence and role fit. Be strict but fair.
        Return only JSON matching this shape:
        {JUDGE_SCHEMA_HINT}
        """
    ).strip()
    return [
        ChatMessage(
            "system",
            build_system_prompt("json_schema", canary, domain=domain, style=style),
        ),
        ChatMessage("user", user),
    ]


def chat_messages(
    technique: str,
    *,
    history: Sequence[ChatMessage],
    user_message: str,
    job_description: str,
    canary: str,
    persona: str = DEFAULT_PERSONA,
    current_question: str = "",
    current_evaluation: str = "",
    domain: str = DEFAULT_DOMAIN,
    style: str = DEFAULT_STYLE,
) -> list[ChatMessage]:
    selected = get_spec(technique)
    selected_persona = get_persona(persona)
    system = build_system_prompt(
        selected.key, canary, domain=domain, style=style
    ) + (
        "\n\nInterviewer style: "
        + selected_persona.label
        + ". "
        + get_persona_instruction(persona)
    )
    messages = [ChatMessage("system", system)]
    messages.extend(history)
    content = user_message.strip()
    if job_description.strip():
        content = (
            _job_description_block(job_description)
            + "\n\n"
            + content
        )
    if current_question.strip():
        content = (
            f"<CurrentQuestion>{escape(current_question.strip())}</CurrentQuestion>\n"
            + content
        )
    if current_evaluation.strip():
        content = (
            "<CurrentEvaluation>"
            + escape(current_evaluation.strip())
            + "</CurrentEvaluation>\n"
            + content
        )
    messages.append(ChatMessage("user", content))
    return messages
