import pytest

pytest.importorskip("chromadb")

from interview_practice.config import Settings
from interview_practice.prompts.schemas import Question
from interview_practice.retrieval import QuestionMemory, memory_collection_name


def _question(question_id: str, text: str) -> Question:
    return Question(
        id=question_id,
        category="technical",
        difficulty="medium",
        question=text,
        why="test",
        answer_points=("one",),
    )


def test_collection_name_is_provider_scoped() -> None:
    assert memory_collection_name("openrouter", "openai/gpt-6-luna") != (
        memory_collection_name("local", "openai/gpt-6-luna")
    )
    assert "openrouter" in memory_collection_name("openrouter", "a/b")


def test_question_memory_detects_near_duplicate(tmp_path) -> None:
    memory = QuestionMemory(
        Settings(provider="demo", question_memory_path=str(tmp_path)),
        path=str(tmp_path),
    )
    question = _question("q1", "How do you evaluate a RAG system?")
    memory.add_questions([question], provider="demo", model="demo/interview-coach")
    assert memory.has_near_duplicate(
        question.question,
        provider="demo",
        model="demo/interview-coach",
    )
    assert not memory.has_near_duplicate(
        "Tell me about a time you handled a production incident.",
        provider="demo",
        model="demo/interview-coach",
    )
