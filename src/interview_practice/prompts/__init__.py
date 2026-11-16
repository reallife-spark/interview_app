"""Prompt techniques, defensive instructions, and structured schemas."""

from interview_practice.prompts.defensive import (
    OFF_TOPIC_REDIRECT,
    defensive_system_prompt,
)
from interview_practice.prompts.schemas import (
    AnswerEvaluation,
    Question,
    QuestionSet,
    SchemaError,
    parse_json_object,
    validate_answer_evaluation,
    validate_question_set,
)
from interview_practice.prompts.templates import (
    ANSWER_EVALUATION_SCHEMA_HINT,
    DEFAULT_TECHNIQUE,
    QUESTION_SET_SCHEMA_HINT,
    TECHNIQUE_ORDER,
    TECHNIQUES,
    Technique,
    answer_evaluation_messages,
    build_system_prompt,
    chain_stage_one_messages,
    chat_messages,
    get_technique,
    question_set_messages,
)

__all__ = [
    "ANSWER_EVALUATION_SCHEMA_HINT",
    "AnswerEvaluation",
    "DEFAULT_TECHNIQUE",
    "OFF_TOPIC_REDIRECT",
    "QUESTION_SET_SCHEMA_HINT",
    "Question",
    "QuestionSet",
    "SchemaError",
    "TECHNIQUES",
    "TECHNIQUE_ORDER",
    "Technique",
    "answer_evaluation_messages",
    "build_system_prompt",
    "chain_stage_one_messages",
    "chat_messages",
    "defensive_system_prompt",
    "get_technique",
    "parse_json_object",
    "question_set_messages",
    "validate_answer_evaluation",
    "validate_question_set",
]
