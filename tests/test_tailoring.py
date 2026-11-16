from interview_practice.tailoring import (
    build_tailored_context,
    chunk_text,
    prepare_job_description,
    select_chunks,
)


def test_prepare_job_description_truncates_visibly() -> None:
    text, truncated, original = prepare_job_description("x" * 9000, max_chars=100)
    assert len(text) == 100
    assert truncated
    assert original == 9000


def test_prepare_empty_job_description() -> None:
    text, truncated, original = prepare_job_description("   ")
    assert text == ""
    assert not truncated
    assert original == 0


def test_chunk_text_respects_limit() -> None:
    text = "\n\n".join(
        [
            "Python and RAG evaluation. " * 20,
            "Kubernetes deployment and GPU scheduling. " * 20,
            "Stakeholder communication and incident review. " * 20,
        ]
    )
    chunks = chunk_text(text, max_chars=120)
    assert chunks
    assert all(len(chunk) <= 120 for chunk in chunks)


def test_select_chunks_prefers_relevant_topic() -> None:
    chunks = (
        "Python and RAG evaluation with labelled data.",
        "Kubernetes deployment and GPU scheduling for inference.",
        "Stakeholder communication and incident review.",
    )
    assert select_chunks("Kubernetes deployment", chunks, top_k=1) == (1,)
    assert select_chunks("RAG evaluation", chunks, top_k=1) == (0,)


def test_tailored_context_uses_whole_short_description() -> None:
    context = build_tailored_context(
        "AI engineer with Python and RAG experience.",
        query="RAG",
        enable_lexical_rag=True,
    )
    assert not context.used_rag
    assert context.text.startswith("AI engineer")
    assert context.notice == ""


def test_tailored_context_uses_rag_for_long_description() -> None:
    paragraphs = [
        "Python and RAG evaluation with labelled data and regression gates. " * 4,
        "Kubernetes deployment, GPU scheduling, and inference capacity planning. " * 4,
        (
            "Stakeholder communication, incident review, and written "
            "decision records. "
        )
        * 4,
        "Prompt engineering, structured output, and safety evaluation. " * 4,
        "Data pipelines, retrieval quality, and embedding drift monitoring. " * 4,
        "Cost controls, rate limits, and production observability. " * 4,
    ]
    job_description = "\n\n".join(paragraphs)
    context = build_tailored_context(
        job_description,
        query="Kubernetes GPU inference",
        enable_lexical_rag=True,
        top_k=3,
    )
    assert context.used_rag
    assert 1 <= context.selected_chunks <= 3
    assert "Kubernetes" in context.text
    assert "RAG-lite" in context.notice


def test_rag_can_be_disabled() -> None:
    context = build_tailored_context(
        "AI engineer with Python and RAG experience. " * 60,
        query="Kubernetes",
        enable_lexical_rag=False,
    )
    assert not context.used_rag
    assert context.text.startswith("AI engineer")
    assert len(context.text) <= 8000
