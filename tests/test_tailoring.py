from interview_practice.tailoring import build_tailored_context


def test_truncation_is_visible() -> None:
    context = build_tailored_context("x" * 9000, query="", max_chars=100)
    assert len(context.text) == 100
    assert context.truncated
    assert context.original_chars == 9000
    assert "truncated" in context.notice.lower()


def test_empty_job_description() -> None:
    context = build_tailored_context("   ", query="")
    assert context.text == ""
    assert not context.truncated
    assert context.original_chars == 0
    assert "No job description" in context.notice


def test_short_description_uses_whole_text() -> None:
    context = build_tailored_context(
        "AI engineer with Python and RAG experience.",
        query="RAG",
        enable_lexical_rag=True,
    )
    assert not context.used_rag
    assert context.text.startswith("AI engineer")
    assert context.notice == ""


def test_rag_lite_selects_relevant_topic() -> None:
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
    context = build_tailored_context(
        "\n\n".join(paragraphs),
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
