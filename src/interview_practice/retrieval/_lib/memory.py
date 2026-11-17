"""Chroma-backed question memory with provider-scoped collections."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from typing import Any

from interview_practice.config import Settings
from interview_practice.prompts.schemas import Question


class MemoryUnavailable(RuntimeError):
    """The optional Chroma dependency or embedding provider is unavailable."""


class HashEmbeddingFunction:
    """Deterministic offline embedding for demo and tests."""

    name = "interview-hash"

    def __call__(self, input: Sequence[str]) -> list[list[float]]:  # noqa: A002
        return [self._embed(text) for text in input]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    @staticmethod
    def _embed(text: str) -> list[float]:
        digest = hashlib.sha256(text.lower().strip().encode("utf-8")).digest()
        values = [byte / 255.0 for byte in digest[:32]]
        return values + [0.0] * 32


def memory_collection_name(provider: str, model: str) -> str:
    raw = f"questions_{provider}_{model.lower()}"
    safe = re.sub(r"[^a-z0-9_-]+", "_", raw).strip("_")
    return safe[:60] or "questions_default"


class QuestionMemory:
    """Store only generated question text, never answers or job descriptions."""

    def __init__(self, settings: Settings, *, path: str | None = None) -> None:
        try:
            import chromadb
        except ImportError as exc:  # pragma: no cover - optional extra
            raise MemoryUnavailable(
                "Question memory requires the chromadb package."
            ) from exc
        self._settings = settings
        try:
            self._client = chromadb.PersistentClient(
                path=path or settings.question_memory_path
            )
        except Exception as exc:
            raise MemoryUnavailable("Could not open the Chroma store.") from exc
        self._collections: dict[tuple[str, str], Any] = {}

    def _embedding(self, provider: str) -> Any:
        if provider == "demo":
            return HashEmbeddingFunction()
        try:
            from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
        except ImportError as exc:  # pragma: no cover
            raise MemoryUnavailable("Chroma embedding support is unavailable.") from exc
        if provider == "openrouter":
            return OpenAIEmbeddingFunction(
                api_key=self._settings.openrouter_api_key,
                model_name=self._settings.embedding_model,
                api_base="https://openrouter.ai/api/v1",
            )
        if provider == "local":
            return OpenAIEmbeddingFunction(
                api_key=self._settings.local_api_key or "local",
                model_name=self._settings.local_embedding_model,
                api_base=self._settings.local_base_url,
            )
        raise MemoryUnavailable(f"Unsupported memory provider: {provider}")

    def _collection(self, provider: str, model: str) -> Any:
        key = (provider, model)
        if key not in self._collections:
            try:
                self._collections[key] = self._client.get_or_create_collection(
                    name=memory_collection_name(provider, model),
                    embedding_function=self._embedding(provider),
                )
            except Exception as exc:
                raise MemoryUnavailable(
                    "Could not open the question-memory collection."
                ) from exc
        return self._collections[key]

    def add_questions(
        self,
        questions: Sequence[Question],
        *,
        provider: str,
        model: str,
    ) -> None:
        if not questions:
            return
        collection = self._collection(provider, model)
        collection.upsert(
            ids=[question.id for question in questions],
            documents=[question.question for question in questions],
            metadatas=[
                {
                    "question_id": question.id,
                    "category": question.category,
                    "difficulty": question.difficulty,
                }
                for question in questions
            ],
        )

    def has_near_duplicate(
        self,
        text: str,
        *,
        provider: str,
        model: str,
        threshold: float = 0.1,
    ) -> bool:
        collection = self._collection(provider, model)
        if collection.count() == 0:
            return False
        try:
            result = collection.query(query_texts=[text], n_results=1)
        except Exception as exc:
            raise MemoryUnavailable("Question-memory query failed.") from exc
        distances = result.get("distances") or []
        if not distances or not distances[0]:
            return False
        distance = distances[0][0]
        return isinstance(distance, (int, float)) and distance < threshold
