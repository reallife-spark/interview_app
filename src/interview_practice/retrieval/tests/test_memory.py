import hashlib
import time

import pytest

pytest.importorskip("chromadb")

from interview_practice.config import Settings
from interview_practice.prompts.schemas import Question
from interview_practice.retrieval import QuestionMemory, memory_collection_name


class FakeEmbedding:
    name = "fake-embedding"

    def __call__(self, input):  # noqa: A002
        return [
            [byte / 255.0 for byte in hashlib.sha256(text.encode()).digest()[:8]]
            for text in input
        ]

    def embed_documents(self, texts):
        return self(texts)

    def embed_query(self, text):
        return self([text])[0]


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.last_post = None

    def post(self, url, **kwargs):
        self.last_post = (url, kwargs)
        return self.response


def _question(question_id: str, text: str) -> Question:
    return Question(
        id=question_id,
        category="technical",
        difficulty="medium",
        question=text,
        why="test",
        answer_points=("one",),
    )


def _memory(tmp_path, **settings_overrides) -> QuestionMemory:
    settings = Settings(
        provider="demo",
        question_memory_path=str(tmp_path),
        **settings_overrides,
    )
    return QuestionMemory(
        settings,
        path=str(tmp_path),
        embedding_function=FakeEmbedding(),
    )


def test_collection_name_is_provider_scoped() -> None:
    assert memory_collection_name("openrouter", "openai/gpt-6-luna") != (
        memory_collection_name("local", "openai/gpt-6-luna")
    )
    assert "openrouter" in memory_collection_name("openrouter", "a/b")
    assert memory_collection_name(
        "openrouter", "a/b", embedding_model="model-one"
    ) != memory_collection_name("openrouter", "a/b", embedding_model="model-two")


def test_question_memory_detects_near_duplicate(tmp_path) -> None:
    memory = _memory(tmp_path)
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


def test_repeated_question_ids_no_longer_overwrite_old_sets(tmp_path) -> None:
    memory = _memory(tmp_path)
    first = _question("q1", "How do you evaluate a RAG system?")
    second = _question("q1", "Tell me about a production incident.")
    memory.add_questions([first], provider="demo", model="demo/interview-coach")
    memory.add_questions([second], provider="demo", model="demo/interview-coach")
    assert memory.count(provider="demo", model="demo/interview-coach") == 2
    assert memory.has_near_duplicate(
        first.question,
        provider="demo",
        model="demo/interview-coach",
    )


def test_question_memory_prunes_to_max_items(tmp_path) -> None:
    memory = _memory(tmp_path, question_memory_max_items=2)
    for index in range(3):
        memory.add_questions(
            [_question(f"q{index}", f"Question number {index} about RAG?")],
            provider="demo",
            model="demo/interview-coach",
        )
        time.sleep(0.01)
    assert memory.count(provider="demo", model="demo/interview-coach") == 2
    assert not memory.has_near_duplicate(
        "Question number 0 about RAG?",
        provider="demo",
        model="demo/interview-coach",
    )


def test_openai_compatible_embedding_request_shape(tmp_path) -> None:
    response = FakeResponse(
        {
            "data": [
                {"index": 0, "embedding": [0.1, 0.2, 0.3]},
            ]
        }
    )
    session = FakeSession(response)
    settings = Settings(
        provider="openrouter",
        openrouter_api_key="test-key",
        embedding_model="qwen/qwen3-embedding-8b",
        question_memory_path=str(tmp_path),
    )
    memory = QuestionMemory(
        settings,
        path=str(tmp_path),
        session=session,
    )
    memory.add_questions(
        [_question("q1", "How do you evaluate a RAG system?")],
        provider="openrouter",
        model="openai/gpt-6-luna",
    )
    url, kwargs = session.last_post
    assert url.endswith("/embeddings")
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert kwargs["json"]["model"] == "qwen/qwen3-embedding-8b"
    assert kwargs["json"]["input"] == ["How do you evaluate a RAG system?"]
    assert memory.count(provider="openrouter", model="openai/gpt-6-luna") == 1
