"""Prompt comparison harness.

The demo mode is a deterministic fixture test of the whole prompt pipeline.
The live mode calls OpenRouter and records the actual model, date and cost.
Neither mode is a general model-quality benchmark.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

from interview_practice.config import COURSE_MODELS, Settings
from interview_practice.cost import default_catalog
from interview_practice.engine import EngineError, InterviewEngine
from interview_practice.prompts.schemas import QuestionSet
from interview_practice.prompts.templates import TECHNIQUE_ORDER
from interview_practice.providers.base import Completion, CompletionRequest
from interview_practice.session import SessionState

CATEGORY_WEIGHT = {
    "technical",
    "behavioural",
    "system-design",
    "role-specific",
    "closing",
}


@dataclass(frozen=True, slots=True)
class EvalCase:
    id: str
    role: str
    job_description: str
    difficulty: str
    count: int


CASES: tuple[EvalCase, ...] = (
    EvalCase(
        id="rag_eval",
        role="AI engineer",
        job_description=(
            "Build and evaluate a RAG service. Own retrieval quality, grounding, "
            "latency, cost and regression gates."
        ),
        difficulty="medium",
        count=3,
    ),
    EvalCase(
        id="behavioural",
        role="AI engineer",
        job_description=(
            "Partner with product and research teams. Explain trade-offs, handle "
            "ambiguity and improve the team's evaluation practice."
        ),
        difficulty="medium",
        count=3,
    ),
    EvalCase(
        id="system_design",
        role="Senior AI engineer",
        job_description=(
            "Design a prompt-evaluation pipeline for a customer-facing assistant. "
            "Cover versioning, safety, cost and rollback."
        ),
        difficulty="hard",
        count=3,
    ),
)


@dataclass(frozen=True, slots=True)
class EvalScore:
    valid: bool
    coverage: float
    specificity: float
    difficulty_match: float
    question_length: float
    count_match: float
    score: float
    notes: str


@dataclass(frozen=True, slots=True)
class EvalRow:
    technique: str
    case_id: str
    provider: str
    model: str
    valid: bool
    coverage: float
    specificity: float
    difficulty_match: float
    question_length: float
    count_match: float
    score: float
    cost_usd: float | None
    notes: str


class ScriptedProvider:
    """Deterministic fixture provider for the offline demo only."""

    name = "demo"

    def __init__(self, technique: str) -> None:
        self.technique = technique
        self.calls = 0

    def list_models(self) -> list[str]:
        return ["scripted/interview-fixture"]

    def complete(self, request: CompletionRequest) -> Completion:
        self.calls += 1
        prompt = request.messages[-1].content if request.messages else ""
        difficulty = _tag(prompt, "Difficulty") or "medium"
        role = _tag(prompt, "Role") or "AI engineer"
        text = _fixture(self.technique, role=role, difficulty=difficulty)
        return Completion(
            text=text,
            model="scripted/interview-fixture",
            provider=self.name,
            latency_ms=0,
            prompt_tokens=len(prompt) // 4,
            completion_tokens=len(text) // 4,
            total_tokens=(len(prompt) + len(text)) // 4,
            cost_usd=0.0,
            finish_reason="stop",
        )


def score_questions(
    question_set: QuestionSet,
    case: EvalCase,
) -> EvalScore:
    count = len(question_set.questions)
    if count == 0:
        return EvalScore(False, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, "empty question set")
    categories = {question.category for question in question_set.questions}
    coverage = min(len(categories & CATEGORY_WEIGHT), 4) / 4
    specificity = sum(
        min(len(question.answer_points), 3) / 3
        for question in question_set.questions
    ) / count
    all_match = all(
        question.difficulty == case.difficulty
        for question in question_set.questions
    )
    difficulty_match = 1.0 if all_match else 0.0
    question_length = sum(
        1.0 if len(question.question) >= 40 else 0.0
        for question in question_set.questions
    ) / count
    count_match = 1.0 if count == case.count else 0.0
    score = 10 * (
        0.30 * coverage
        + 0.30 * specificity
        + 0.15 * difficulty_match
        + 0.15 * question_length
        + 0.10 * count_match
    )
    return EvalScore(
        valid=True,
        coverage=coverage,
        specificity=specificity,
        difficulty_match=difficulty_match,
        question_length=question_length,
        count_match=count_match,
        score=round(score, 2),
        notes="parsed",
    )


def run_demo() -> list[EvalRow]:
    rows: list[EvalRow] = []
    for technique in TECHNIQUE_ORDER:
        engine = InterviewEngine(
            Settings(
                provider="demo",
                max_calls=50,
                max_tokens=350,
                max_output_tokens=350,
            ),
            provider=ScriptedProvider(technique),
            session=SessionState(),
            catalog=default_catalog(),
        )
        for case in CASES:
            try:
                result = engine.generate_questions(
                    role=case.role,
                    job_description=case.job_description,
                    difficulty=case.difficulty,
                    count=case.count,
                    technique=technique,
                )
            except (EngineError, ValueError) as exc:
                rows.append(_invalid_row(technique, case, "demo", "scripted", str(exc)))
            else:
                score = score_questions(result.question_set, case)
                rows.append(
                    _row(
                        technique=technique,
                        case=case,
                        provider="demo",
                        model=result.completion.model,
                        score=score,
                        cost=result.completion.cost_usd,
                    )
                )
    return rows


def run_live(*, model: str | None = None) -> list[EvalRow]:
    settings = Settings.from_env()
    selected_model = model or settings.model
    if selected_model not in COURSE_MODELS:
        raise EngineError(f"Model must be one of {', '.join(COURSE_MODELS)}")
    if not settings.openrouter_api_key:
        raise EngineError("OPENROUTER_API_KEY is required for a live evaluation")
    live_settings = Settings(
        provider="openrouter",
        model=selected_model,
        temperature=0.3,
        max_tokens=350,
        max_output_tokens=350,
        max_calls=50,
        session_cost_cap_usd=1.00,
        openrouter_api_key=settings.openrouter_api_key,
        strict_safety=False,
        enable_lexical_rag=False,
        max_input_chars=8000,
    )
    engine = InterviewEngine(
        live_settings,
        session=SessionState(),
        catalog=default_catalog(),
    )
    rows: list[EvalRow] = []
    for technique in TECHNIQUE_ORDER:
        for case in CASES:
            try:
                result = engine.generate_questions(
                    role=case.role,
                    job_description=case.job_description,
                    difficulty=case.difficulty,
                    count=case.count,
                    technique=technique,
                )
            except (EngineError, ValueError) as exc:
                rows.append(
                    _invalid_row(
                        technique,
                        case,
                        "openrouter",
                        selected_model,
                        str(exc),
                    )
                )
            else:
                score = score_questions(result.question_set, case)
                rows.append(
                    _row(
                        technique=technique,
                        case=case,
                        provider="openrouter",
                        model=result.completion.model,
                        score=score,
                        cost=result.completion.cost_usd,
                    )
                )
    return rows


def write_results(rows: list[EvalRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))


def summarise(rows: list[EvalRow]) -> list[tuple[str, float, int, int]]:
    grouped: dict[str, list[EvalRow]] = defaultdict(list)
    for row in rows:
        grouped[row.technique].append(row)
    summary = []
    for technique, items in grouped.items():
        average = sum(item.score for item in items) / len(items)
        valid = sum(1 for item in items if item.valid)
        total = len(items)
        summary.append((technique, round(average, 2), valid, total))
    return sorted(summary, key=lambda item: item[1], reverse=True)


def write_summary(
    rows: list[EvalRow],
    path: Path,
    *,
    mode: str,
    model: str,
) -> str:
    summary = summarise(rows)
    best = summary[0][0] if summary else "none"
    lines = [
        "# Prompt evaluation",
        "",
        f"- Mode: **{mode}**",
        f"- Date: **{date.today().isoformat()}**",
        f"- Model: **{model}**",
        f"- Cases: **{len(CASES)}** per technique",
        f"- Techniques: **{len(TECHNIQUE_ORDER)}**",
        "",
        "## Ranking",
        "",
        "| Rank | Technique | Average score / 10 | Valid rows |",
        "|---:|---|---:|---:|",
    ]
    for index, (technique, average, valid, total) in enumerate(summary, start=1):
        lines.append(f"| {index} | {technique} | {average:.2f} | {valid}/{total} |")
    lines.extend(
        [
            "",
            f"**Best in this run:** `{best}`",
            "",
            "## Method",
            "",
            "Each technique generated a question set for three cases: RAG evaluation,",
            "behavioural collaboration, and a senior system-design prompt. The",
            "deterministic rubric weights coverage (30%), answer-point specificity",
            "(30%), difficulty match (15%), question length (15%) and requested",
            "count (10%). The score is a pipeline and shape check, not a claim about",
            "the model's general quality.",
            "",
        ]
    )
    if mode == "demo":
        lines.extend(
            [
                "## Limitation",
                "",
                "This is an **offline fixture run**. The scripted provider is designed",
                "to exercise parsing, guardrails and scoring; it is not a live model",
                "comparison. Run `python scripts/evaluate_prompts.py --live` with an",
                "OpenRouter key for a dated live sample.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Limitation",
                "",
                "This is a **small live sample**. It records the model, date and",
                "observed rows, but it does not establish general model quality.",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return best


def _row(
    *,
    technique: str,
    case: EvalCase,
    provider: str,
    model: str,
    score: EvalScore,
    cost: float | None,
) -> EvalRow:
    return EvalRow(
        technique=technique,
        case_id=case.id,
        provider=provider,
        model=model,
        valid=score.valid,
        coverage=round(score.coverage, 3),
        specificity=round(score.specificity, 3),
        difficulty_match=score.difficulty_match,
        question_length=round(score.question_length, 3),
        count_match=score.count_match,
        score=score.score,
        cost_usd=cost,
        notes=score.notes,
    )


def _invalid_row(
    technique: str,
    case: EvalCase,
    provider: str,
    model: str,
    note: str,
) -> EvalRow:
    return EvalRow(
        technique=technique,
        case_id=case.id,
        provider=provider,
        model=model,
        valid=False,
        coverage=0.0,
        specificity=0.0,
        difficulty_match=0.0,
        question_length=0.0,
        count_match=0.0,
        score=0.0,
        cost_usd=None,
        notes=note[:160],
    )


def _tag(prompt: str, tag: str) -> str | None:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", prompt, re.DOTALL)
    return match.group(1).strip() if match else None


def _fixture(technique: str, *, role: str, difficulty: str) -> str:
    categories = {
        "zero_shot": ("technical", "technical", "closing"),
        "role_persona": ("technical", "behavioural", "system-design"),
        "few_shot": ("technical", "behavioural", "system-design"),
        "cot": ("technical", "behavioural", "system-design"),
        "json_schema": ("technical", "behavioural", "system-design"),
        "chained": ("technical", "role-specific", "closing"),
    }.get(technique, ("technical", "behavioural", "system-design"))
    points = {
        "zero_shot": 1,
        "role_persona": 2,
        "few_shot": 2,
        "cot": 2,
        "json_schema": 3,
        "chained": 2,
    }.get(technique, 2)
    question_text = {
        "technical": "How would you evaluate retrieval quality and groundedness?",
        "behavioural": "Tell me about a time you changed a design after user feedback.",
        "system-design": "Design a prompt-evaluation pipeline with release gates.",
        "role-specific": "Which AI-engineering trade-off would you prioritise first?",
        "closing": "What questions would you ask the hiring team at the end?",
    }
    why = (
        "This case tests a concrete interview skill and gives the candidate a "
        "specific area to practise."
    )
    questions = []
    for index, category in enumerate(categories, start=1):
        questions.append(
            {
                "id": f"q{index}",
                "category": category,
                "difficulty": difficulty,
                "question": question_text[category],
                "why": why,
                "answer_points": [
                    f"point {point} for {category}" for point in range(1, points + 1)
                ],
            }
        )
    return json.dumps({"role": role, "questions": questions}, indent=2)
