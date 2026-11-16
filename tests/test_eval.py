import csv
from pathlib import Path

import pytest

from interview_practice.engine import EngineError
from interview_practice.evaluation import (
    CASES,
    EvalCase,
    run_demo,
    run_live,
    score_questions,
    summarise,
    write_results,
    write_summary,
)
from interview_practice.prompts.schemas import Question, QuestionSet


def _question_set(count: int = 3, difficulty: str = "medium") -> QuestionSet:
    return QuestionSet(
        role="AI engineer",
        questions=tuple(
            Question(
                id=f"q{index}",
                category=("technical", "behavioural", "system-design")[index % 3],
                difficulty=difficulty,
                question="How would you evaluate retrieval quality and groundedness?",
                why="Tests a concrete interview skill with a specific practice area.",
                answer_points=("retrieval", "grounding", "release gate"),
            )
            for index in range(1, count + 1)
        ),
    )


def test_score_questions_rewards_shape() -> None:
    case = EvalCase(
        "x",
        "AI engineer",
        "jd",
        "medium",
        3,
        expected_concepts=("retrieval", "groundedness"),
    )
    score = score_questions(_question_set(), case)
    assert score.valid
    assert score.score > 8.0
    assert score.coverage == 0.75
    assert score.concept_coverage == 1.0
    assert score.shape_score > 8.0


def test_score_questions_rejects_empty_set() -> None:
    score = score_questions(QuestionSet("AI engineer", ()), CASES[0])
    assert not score.valid
    assert score.score == 0.0


def test_run_demo_has_all_rows_and_a_winner() -> None:
    rows = run_demo()
    assert len(rows) == 18
    assert all(row.valid for row in rows)
    ranking = summarise(rows)
    assert ranking[0][0] == "json_schema"
    assert ranking[0][1] > ranking[-1][1]


def test_results_and_summary_are_written(tmp_path: Path) -> None:
    rows = run_demo()
    results = tmp_path / "results.csv"
    summary = tmp_path / "summary.md"
    write_results(rows, results)
    write_summary(rows, summary, mode="demo", model="scripted")
    with results.open(encoding="utf-8") as handle:
        reader = list(csv.DictReader(handle))
    assert len(reader) == 18
    assert "technique" in reader[0]
    text = summary.read_text(encoding="utf-8")
    assert "demo" in text
    assert "json_schema" in text


def test_live_requires_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(EngineError, match="OPENROUTER_API_KEY"):
        run_live()
