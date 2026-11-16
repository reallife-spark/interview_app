"""Public prompt-construction facade."""

from __future__ import annotations

from collections.abc import Sequence

from interview_practice.messages import ChatMessage
from interview_practice.prompts._lib.catalog import (
    DEFAULT_TECHNIQUE,
    TECHNIQUE_ORDER,
    get_spec,
    technique_options,
)
from interview_practice.prompts._lib.personas import (
    DEFAULT_PERSONA,
    PERSONA_ORDER,
    get_persona,
    persona_options,
)
from interview_practice.prompts._lib.templates import (
    answer_evaluation_messages,
    build_system_prompt,
    chain_stage_one_messages,
    chat_messages,
    question_set_messages,
)
from interview_practice.prompts.personas import Persona
from interview_practice.prompts.techniques import PROMPT_VERSION, Technique


class PromptLibrary:
    """Small interface over the prompt techniques and message builders."""

    @property
    def version(self) -> str:
        return PROMPT_VERSION

    @property
    def default_technique(self) -> str:
        return DEFAULT_TECHNIQUE

    @property
    def technique_order(self) -> tuple[str, ...]:
        return TECHNIQUE_ORDER

    def techniques(self) -> tuple[Technique, ...]:
        return technique_options()

    def get_technique(self, key: str) -> Technique:
        spec = get_spec(key)
        return Technique(key=spec.key, label=spec.label, description=spec.description)

    @property
    def default_persona(self) -> str:
        return DEFAULT_PERSONA

    @property
    def persona_order(self) -> tuple[str, ...]:
        return PERSONA_ORDER

    def personas(self) -> tuple[Persona, ...]:
        return persona_options()

    def get_persona(self, key: str) -> Persona:
        return get_persona(key)

    def system_prompt(self, technique: str, canary: str) -> str:
        return build_system_prompt(technique, canary)

    def question_set(
        self,
        technique: str,
        *,
        role: str,
        job_description: str,
        difficulty: str,
        count: int,
        canary: str,
        requirements: str = "",
    ) -> list[ChatMessage]:
        return question_set_messages(
            technique,
            role=role,
            job_description=job_description,
            difficulty=difficulty,
            count=count,
            canary=canary,
            requirements=requirements,
        )

    def chain_stage_one(
        self,
        *,
        role: str,
        job_description: str,
        canary: str,
    ) -> list[ChatMessage]:
        return chain_stage_one_messages(
            role=role,
            job_description=job_description,
            canary=canary,
        )

    def answer_evaluation(
        self,
        technique: str,
        *,
        question: str,
        answer: str,
        job_description: str,
        canary: str,
    ) -> list[ChatMessage]:
        return answer_evaluation_messages(
            technique,
            question=question,
            answer=answer,
            job_description=job_description,
            canary=canary,
        )

    def chat(
        self,
        technique: str,
        *,
        history: Sequence[ChatMessage],
        user_message: str,
        job_description: str,
        canary: str,
        persona: str = DEFAULT_PERSONA,
    ) -> list[ChatMessage]:
        return chat_messages(
            technique,
            history=history,
            user_message=user_message,
            job_description=job_description,
            canary=canary,
            persona=persona,
        )
