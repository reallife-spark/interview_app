"""Job-description tailoring with a bounded lexical RAG-lite path.

This is deliberately not a vector database. It is a transparent lexical
retriever that keeps the whole description when it is short and selects the
most relevant chunks when the description is long.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

MAX_JOB_DESCRIPTION_CHARS = 8000
DEFAULT_CHUNK_CHARS = 1200
DEFAULT_TOP_K = 3
MIN_RAG_CHARS = 1200
_WORD_RE = re.compile(r"[a-z0-9][a-z0-9+#.-]*")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True, slots=True)
class TailoredContext:
    text: str
    original_chars: int
    truncated: bool
    used_rag: bool
    selected_chunks: int
    max_chars: int

    @property
    def notice(self) -> str:
        parts: list[str] = []
        if not self.text.strip():
            parts.append("No job description provided; using role-level preparation.")
        if self.truncated:
            parts.append(
                f"Job description truncated from {self.original_chars} to "
                f"{self.max_chars} characters."
            )
        if self.used_rag:
            parts.append(
                f"Using {self.selected_chunks} relevant job-description chunks "
                "(lexical RAG-lite)."
            )
        return " ".join(parts)


def _prepare_job_description(
    text: str,
    *,
    max_chars: int = MAX_JOB_DESCRIPTION_CHARS,
) -> tuple[str, bool, int]:
    """Return (capped text, truncated flag, original length)."""

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    cleaned = text.strip()
    original_chars = len(cleaned)
    if original_chars <= max_chars:
        return cleaned, False, original_chars
    return cleaned[:max_chars].rstrip(), True, original_chars


def _chunk_text(
    text: str,
    *,
    max_chars: int = DEFAULT_CHUNK_CHARS,
) -> tuple[str, ...]:
    """Split text into deterministic paragraph/sentence chunks."""

    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    cleaned = text.strip()
    if not cleaned:
        return ()
    paragraphs = [
        part.strip()
        for part in re.split(r"\n\s*\n", cleaned)
        if part.strip()
    ]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        for piece in _split_oversized(paragraph, max_chars):
            candidate = f"{current}\n\n{piece}".strip() if current else piece
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = piece
    if current:
        chunks.append(current)
    return tuple(chunks)


def _select_chunks(
    query: str,
    chunks: tuple[str, ...],
    *,
    top_k: int = DEFAULT_TOP_K,
) -> tuple[int, ...]:
    """Rank chunks with a small BM25-style lexical score."""

    if top_k <= 0 or not chunks:
        return ()
    query_tokens = _tokens(query)
    if not query_tokens:
        return tuple(range(min(top_k, len(chunks))))
    tokenized = [_tokens(chunk) for chunk in chunks]
    scores = _bm25_scores(query_tokens, tokenized)
    ranked = sorted(range(len(chunks)), key=lambda index: scores[index], reverse=True)
    return tuple(ranked[: min(top_k, len(chunks))])


def build_tailored_context(
    job_description: str,
    *,
    query: str,
    enable_lexical_rag: bool = False,
    max_chars: int = MAX_JOB_DESCRIPTION_CHARS,
    top_k: int = DEFAULT_TOP_K,
) -> TailoredContext:
    capped, truncated, original_chars = _prepare_job_description(
        job_description, max_chars=max_chars
    )
    if not capped:
        return TailoredContext(
            text="",
            original_chars=original_chars,
            truncated=False,
            used_rag=False,
            selected_chunks=0,
            max_chars=max_chars,
        )
    if not enable_lexical_rag or len(capped) < MIN_RAG_CHARS:
        return TailoredContext(
            text=capped,
            original_chars=original_chars,
            truncated=truncated,
            used_rag=False,
            selected_chunks=0,
            max_chars=max_chars,
        )
    chunks = _chunk_text(capped)
    selected = _select_chunks(query, chunks, top_k=top_k)
    if not selected:
        return TailoredContext(
            text=capped,
            original_chars=original_chars,
            truncated=truncated,
            used_rag=False,
            selected_chunks=0,
            max_chars=max_chars,
        )
    chosen = [chunks[index] for index in selected]
    return TailoredContext(
        text="\n\n---\n\n".join(chosen),
        original_chars=original_chars,
        truncated=truncated,
        used_rag=True,
        selected_chunks=len(chosen),
        max_chars=max_chars,
    )


def _split_oversized(text: str, max_chars: int) -> tuple[str, ...]:
    if len(text) <= max_chars:
        return (text,)
    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_RE.split(text):
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                pieces.append(current)
            if len(sentence) > max_chars:
                pieces.extend(
                    sentence[start : start + max_chars]
                    for start in range(0, len(sentence), max_chars)
                )
                current = ""
            else:
                current = sentence
    if current:
        pieces.append(current)
    return tuple(pieces)


def _tokens(text: str) -> list[str]:
    return [match.group(0) for match in _WORD_RE.finditer(text.lower())]


def _bm25_scores(
    query_tokens: list[str],
    documents: list[list[str]],
    *,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[float]:
    if not documents:
        return []
    doc_count = len(documents)
    avg_length = sum(len(document) for document in documents) / doc_count or 1.0
    document_frequency: Counter[str] = Counter()
    for document in documents:
        document_frequency.update(set(document))
    scores: list[float] = []
    for document in documents:
        length = len(document) or 1
        frequencies = Counter(document)
        score = 0.0
        for token in query_tokens:
            frequency = frequencies.get(token, 0)
            if frequency == 0:
                continue
            df = document_frequency[token]
            idf = math.log(1 + (doc_count - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (1 - b + b * length / avg_length)
            score += idf * (frequency * (k1 + 1)) / denominator
        scores.append(score)
    return scores
