"""Chroma-backed question memory with provider-scoped collections."""

from __future__ import annotations

import hashlib
import re
import time
from collections.abc import Sequence
from typing import Any

import requests

from interview_practice.config import OPENROUTER_BASE_URL, Settings
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


class OpenAICompatibleEmbeddingFunction:
    """Small Chroma embedding adapter for OpenRouter and local endpoints.

    Chroma 0.6.3's bundled OpenAIEmbeddingFunction only supports the openai
    1.x client shape. The project installs openai 2.x, so this adapter uses the
    OpenAI-compatible HTTP endpoint directly.
    """

    name = "interview-openai-compatible"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = 30.0,
        session: Any | None = None,
    ) -> None:
        if not base_url:
            raise MemoryUnavailable("An embedding base URL is required.")
        if not model:
            raise MemoryUnavailable("An embedding model is required.")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._session = session or requests.Session()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def __call__(self, input: Sequence[str]) -> list[list[float]]:  # noqa: A002
        texts = [str(text) for text in input]
        if not texts:
            return []
        try:
            response = self._session.post(
                f"{self._base_url}/embeddings",
                headers=self._headers(),
                json={"model": self._model, "input": texts},
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise MemoryUnavailable(
                "Could not reach the embedding endpoint."
            ) from exc
        if response.status_code >= 400:
            raise MemoryUnavailable(
                f"Embedding request failed ({response.status_code})."
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise MemoryUnavailable(
                "Embedding endpoint returned invalid JSON."
            ) from exc
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list) or not data:
            raise MemoryUnavailable("Embedding endpoint returned no embeddings.")
        rows = [
            item
            for item in data
            if isinstance(item, dict) and isinstance(item.get("embedding"), list)
        ]
        if len(rows) != len(texts):
            raise MemoryUnavailable(
                "Embedding count did not match the input count."
            )
        rows.sort(key=lambda item: item.get("index", 0))
        return [list(item["embedding"]) for item in rows]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self(texts)

    def embed_query(self, text: str) -> list[float]:
        return self([text])[0]


def memory_collection_name(
    provider: str,
    model: str,
    *,
    embedding_model: str = "",
) -> str:
    raw = f"questions_v2_{provider}_{model.lower()}"
    if embedding_model:
        digest = hashlib.sha256(embedding_model.lower().encode("utf-8")).hexdigest()
        raw += f"_{digest[:8]}"
    safe = re.sub(r"[^a-z0-9_-]+", "_", raw).strip("_")
    return safe[:60] or "questions_default"


class QuestionMemory:
    """Store only generated question text, never answers or job descriptions."""

    def __init__(
        self,
        settings: Settings,
        *,
        path: str | None = None,
        session: Any | None = None,
        embedding_function: Any | None = None,
    ) -> None:
        try:
            import chromadb
        except ImportError as exc:  # pragma: no cover - optional extra
            raise MemoryUnavailable(
                "Question memory requires the chromadb package."
            ) from exc
        self._settings = settings
        self._session = session
        self._embedding_override = embedding_function
        try:
            self._client = chromadb.PersistentClient(
                path=path or settings.question_memory_path
            )
        except Exception as exc:
            raise MemoryUnavailable("Could not open the Chroma store.") from exc
        self._collections: dict[tuple[str, str], Any] = {}

    def _embedding(self, provider: str) -> Any:
        if self._embedding_override is not None:
            return self._embedding_override
        if provider == "demo":
            return HashEmbeddingFunction()
        if provider == "openrouter":
            return OpenAICompatibleEmbeddingFunction(
                base_url=OPENROUTER_BASE_URL,
                api_key=self._settings.openrouter_api_key,
                model=self._settings.embedding_model,
                session=self._session,
            )
        if provider == "local":
            return OpenAICompatibleEmbeddingFunction(
                base_url=self._settings.local_base_url,
                api_key=self._settings.local_api_key or "local",
                model=self._settings.local_embedding_model,
                session=self._session,
            )
        raise MemoryUnavailable(f"Unsupported memory provider: {provider}")

    def _embedding_model(self, provider: str) -> str:
        if provider == "openrouter":
            return self._settings.embedding_model
        if provider == "local":
            return self._settings.local_embedding_model
        return ""

    def _collection(self, provider: str, model: str) -> Any:
        key = (provider, model)
        if key not in self._collections:
            try:
                self._collections[key] = self._client.get_or_create_collection(
                    name=memory_collection_name(
                        provider,
                        model,
                        embedding_model=self._embedding_model(provider),
                    ),
                    embedding_function=self._embedding(provider),
                    metadata={"hnsw:space": "cosine"},
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
        now = time.time()
        collection.upsert(
            ids=[_question_document_id(question) for question in questions],
            documents=[question.question for question in questions],
            metadatas=[
                {
                    "question_id": question.id,
                    "category": question.category,
                    "difficulty": question.difficulty,
                    "created_at": now + index * 1e-6,
                }
                for index, question in enumerate(questions)
            ],
        )
        self._prune(collection)

    def _prune(self, collection: Any) -> None:
        max_items = self._settings.question_memory_max_items
        if max_items <= 0:
            return
        count = collection.count()
        if count <= max_items:
            return
        payload = collection.get(include=["metadatas"])
        ids = payload.get("ids") or []
        metadatas = payload.get("metadatas") or []
        rows = list(zip(ids, metadatas, strict=False))
        rows.sort(key=lambda row: float((row[1] or {}).get("created_at", 0.0)))
        remove = [row[0] for row in rows[: count - max_items]]
        if remove:
            collection.delete(ids=remove)

    def count(self, *, provider: str, model: str) -> int:
        return self._collection(provider, model).count()

    def has_near_duplicate(
        self,
        text: str,
        *,
        provider: str,
        model: str,
        threshold: float | None = None,
    ) -> bool:
        collection = self._collection(provider, model)
        if collection.count() == 0:
            return False
        try:
            result = collection.query(
                query_texts=[text],
                n_results=1,
                include=["distances"],
            )
        except Exception as exc:
            raise MemoryUnavailable("Question-memory query failed.") from exc
        distances = result.get("distances") or []
        if not distances or not distances[0]:
            return False
        distance = distances[0][0]
        limit = (
            self._settings.question_memory_duplicate_distance
            if threshold is None
            else threshold
        )
        return isinstance(distance, (int, float)) and distance < limit


def _question_document_id(question: Question) -> str:
    text = question.question.strip().lower()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
