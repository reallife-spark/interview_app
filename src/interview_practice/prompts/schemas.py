"""Structured output schemas for question sets and answer evaluations."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

QUESTION_CATEGORIES = {
    "technical",
    "behavioural",
    "system-design",
    "role-specific",
    "closing",
}
DIFFICULTIES = {"easy", "medium", "hard"}


class SchemaError(ValueError):
    """The model output did not match the promised JSON shape."""


@dataclass(frozen=True, slots=True)
class Question:
    id: str
    category: str
    difficulty: str
    question: str
    why: str
    answer_points: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "difficulty": self.difficulty,
            "question": self.question,
            "why": self.why,
            "answer_points": list(self.answer_points),
        }


@dataclass(frozen=True, slots=True)
class QuestionSet:
    role: str
    questions: tuple[Question, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "questions": [question.to_dict() for question in self.questions],
        }


@dataclass(frozen=True, slots=True)
class AnswerEvaluation:
    score: int
    summary: str
    strengths: tuple[str, ...]
    gaps: tuple[str, ...]
    improved_answer: str
    next_steps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "summary": self.summary,
            "strengths": list(self.strengths),
            "gaps": list(self.gaps),
            "improved_answer": self.improved_answer,
            "next_steps": list(self.next_steps),
        }


def parse_json_object(text: str) -> dict[str, Any]:
    """Extract one JSON object from a model reply.

    Accepts a bare object, a fenced object, or text with a short preamble.
    Rejects arrays, empty input and invalid JSON.
    """

    if not isinstance(text, str) or not text.strip():
        raise SchemaError("response is empty")
    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise SchemaError("response does not contain a JSON object")
    try:
        payload = json.loads(candidate[start : end + 1])
    except json.JSONDecodeError as exc:
        raise SchemaError("response contains invalid JSON") from exc
    if not isinstance(payload, dict):
        raise SchemaError("response JSON must be an object")
    return payload


def validate_question_set(payload: Mapping[str, Any]) -> QuestionSet:
    role = _required_text(payload, "role")
    raw_questions = payload.get("questions")
    if not isinstance(raw_questions, list) or not raw_questions:
        raise SchemaError("questions must be a non-empty list")
    if len(raw_questions) > 10:
        raise SchemaError("questions must contain at most 10 items")
    questions = []
    seen_ids = set()
    for index, raw in enumerate(raw_questions):
        if not isinstance(raw, Mapping):
            raise SchemaError(f"question {index} must be an object")
        question_id = _required_text(raw, "id")
        if question_id in seen_ids:
            raise SchemaError(f"duplicate question id: {question_id}")
        seen_ids.add(question_id)
        category = _required_text(raw, "category")
        if category not in QUESTION_CATEGORIES:
            raise SchemaError(f"unknown question category: {category}")
        difficulty = _required_text(raw, "difficulty")
        if difficulty not in DIFFICULTIES:
            raise SchemaError(f"unknown difficulty: {difficulty}")
        points = raw.get("answer_points")
        if not isinstance(points, list) or not points:
            raise SchemaError(f"question {index} needs answer_points")
        cleaned_points = tuple(
            value.strip()
            for value in points
            if isinstance(value, str) and value.strip()
        )
        if len(cleaned_points) != len(points) or len(cleaned_points) > 6:
            raise SchemaError(f"question {index} has invalid answer_points")
        questions.append(
            Question(
                id=question_id,
                category=category,
                difficulty=difficulty,
                question=_required_text(raw, "question"),
                why=_required_text(raw, "why"),
                answer_points=cleaned_points,
            )
        )
    return QuestionSet(role=role, questions=tuple(questions))


def validate_answer_evaluation(payload: Mapping[str, Any]) -> AnswerEvaluation:
    score = payload.get("score")
    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        raise SchemaError("score must be an integer between 0 and 100")
    return AnswerEvaluation(
        score=score,
        summary=_required_text(payload, "summary"),
        strengths=_text_list(payload, "strengths"),
        gaps=_text_list(payload, "gaps"),
        improved_answer=_required_text(payload, "improved_answer"),
        next_steps=_text_list(payload, "next_steps"),
    )


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SchemaError(f"{key} must be a non-empty string")
    return value.strip()


def _text_list(payload: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise SchemaError(f"{key} must be a non-empty list")
    cleaned = tuple(
        item.strip() for item in value if isinstance(item, str) and item.strip()
    )
    if len(cleaned) != len(value):
        raise SchemaError(f"{key} must contain only non-empty strings")
    return cleaned
