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


RUBRIC_KEYS = {
    "technical_depth",
    "problem_solving",
    "communication",
    "role_fit",
    "collaboration",
    "ownership",
}


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


@dataclass(frozen=True, slots=True)
class RubricCriterion:
    key: str
    label: str
    weight: int
    descriptors: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "weight": self.weight,
            "descriptors": list(self.descriptors),
        }


@dataclass(frozen=True, slots=True)
class JudgeCriterion:
    name: str
    score: int
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": self.score,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class JudgeScore:
    score: int
    verdict: str
    criteria: tuple[JudgeCriterion, ...]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "verdict": self.verdict,
            "criteria": [item.to_dict() for item in self.criteria],
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class InterviewRubric:
    role: str
    criteria: tuple[RubricCriterion, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "criteria": [criterion.to_dict() for criterion in self.criteria],
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


def validate_judge_score(payload: Mapping[str, Any]) -> JudgeScore:
    score = payload.get("score")
    if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
        raise SchemaError("judge score must be an integer between 0 and 100")
    verdict = _required_text(payload, "verdict")
    rationale = _required_text(payload, "rationale")
    raw_criteria = payload.get("criteria")
    if not isinstance(raw_criteria, list) or not 2 <= len(raw_criteria) <= 6:
        raise SchemaError("judge criteria must contain 2 to 6 items")
    criteria = []
    for index, raw in enumerate(raw_criteria):
        if not isinstance(raw, Mapping):
            raise SchemaError(f"judge criterion {index} must be an object")
        item_score = raw.get("score")
        if (
            not isinstance(item_score, int)
            or isinstance(item_score, bool)
            or not 0 <= item_score <= 100
        ):
            raise SchemaError(f"judge criterion {index} score must be 0-100")
        criteria.append(
            JudgeCriterion(
                name=_required_text(raw, "name"),
                score=item_score,
                rationale=_required_text(raw, "rationale"),
            )
        )
    return JudgeScore(
        score=score,
        verdict=verdict,
        criteria=tuple(criteria),
        rationale=rationale,
    )


def validate_interview_rubric(payload: Mapping[str, Any]) -> InterviewRubric:
    role = _required_text(payload, "role")
    raw_criteria = payload.get("criteria")
    if not isinstance(raw_criteria, list) or not 4 <= len(raw_criteria) <= 6:
        raise SchemaError("criteria must contain 4 to 6 items")
    criteria: list[RubricCriterion] = []
    seen: set[str] = set()
    total = 0
    for index, raw in enumerate(raw_criteria):
        if not isinstance(raw, Mapping):
            raise SchemaError(f"criterion {index} must be an object")
        key = _required_text(raw, "key")
        if key not in RUBRIC_KEYS:
            raise SchemaError(f"unknown rubric key: {key}")
        if key in seen:
            raise SchemaError(f"duplicate rubric key: {key}")
        seen.add(key)
        weight = raw.get("weight")
        if (
            not isinstance(weight, int)
            or isinstance(weight, bool)
            or not 1 <= weight <= 100
        ):
            raise SchemaError(f"criterion {index} weight must be 1-100")
        descriptors = raw.get("descriptors")
        if not isinstance(descriptors, list) or len(descriptors) < 2:
            raise SchemaError(f"criterion {index} needs two descriptors")
        clean = tuple(
            value.strip()
            for value in descriptors
            if isinstance(value, str) and value.strip()
        )
        if len(clean) != len(descriptors):
            raise SchemaError(f"criterion {index} has invalid descriptors")
        total += weight
        criteria.append(
            RubricCriterion(
                key=key,
                label=_required_text(raw, "label"),
                weight=weight,
                descriptors=clean,
            )
        )
    if total != 100:
        raise SchemaError("rubric weights must total 100")
    return InterviewRubric(role=role, criteria=tuple(criteria))


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
