"""Single-page Streamlit layout.

The engine is deliberately separate from this module so the provider, prompt,
safety and budget behaviour can be tested without a browser.
"""

from __future__ import annotations

from dataclasses import replace

import streamlit as st

from interview_practice.config import (
    ALLOWED_REASONING_EFFORTS,
    COURSE_MODELS,
    Settings,
    apply_secret_values,
)
from interview_practice.cost import format_usd
from interview_practice.engine import (
    EngineError,
    EvaluationResult,
    InterviewEngine,
    QuestionGenerationResult,
)
from interview_practice.prompts.templates import (
    DEFAULT_TECHNIQUE,
    TECHNIQUE_ORDER,
    TECHNIQUES,
)
from interview_practice.providers import PROVIDER_NAMES
from interview_practice.session import SessionState

PROVIDER_LABELS = {
    "demo": "Demo — no key",
    "openrouter": "OpenRouter — public",
    "local": "Local agx64 — developer",
}
MODEL_INDEX = {model: index for index, model in enumerate(COURSE_MODELS)}


def _runtime_settings() -> Settings:
    """Read env first, then merge Streamlit Cloud secrets."""

    base = Settings.from_env()
    try:
        values = dict(st.secrets)
    except Exception:
        return base
    return apply_secret_values(base, values)


def render_app() -> None:
    st.set_page_config(
        page_title="Interview Practice Coach",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    base = _runtime_settings()
    session = _session()
    settings, technique = _sidebar(base, session)
    try:
        engine = InterviewEngine(
            settings,
            session=session,
            catalog=st.session_state.get("catalog"),
        )
    except EngineError as exc:
        st.error(str(exc))
        st.stop()
        return

    if settings.provider == "openrouter":
        if st.sidebar.button("Refresh OpenRouter prices", use_container_width=True):
            if engine.refresh_catalog():
                st.session_state["catalog"] = engine.catalog
                st.sidebar.success("Model prices refreshed.")
            else:
                st.sidebar.warning(
                    "Could not refresh prices; estimates may be unavailable."
                )
        _show_stats(session, settings)

    st.title("Interview Practice Coach")
    st.caption("Turing College Sprint 1 · job-description-tailored interview practice")
    st.write(
        "Prepare questions, practise a written answer, and use the coach for "
        "follow-up work. Job descriptions and answers are treated as data, not "
        "instructions."
    )

    tabs = st.tabs(["1 · Prepare", "2 · Practice", "3 · Coach"])
    with tabs[0]:
        _prepare_tab(engine, technique)
    with tabs[1]:
        _practice_tab(engine, technique)
    with tabs[2]:
        _coach_tab(engine, technique)

    st.divider()
    st.caption(
        "Session-only history. No chat is saved. Demo mode makes no network "
        "calls. OpenRouter mode sends the prompt and job description to "
        "OpenRouter."
    )


def _session() -> SessionState:
    if "session" not in st.session_state:
        st.session_state.session = SessionState()
    return st.session_state.session


def _sidebar(base: Settings, session: SessionState) -> tuple[Settings, str]:
    st.sidebar.header("Settings")
    with st.sidebar.expander("Developer settings", expanded=True):
        provider = st.selectbox(
            "Provider",
            PROVIDER_NAMES,
            index=PROVIDER_NAMES.index(base.provider),
            format_func=lambda name: PROVIDER_LABELS[name],
            key="provider",
        )

        model = base.model
        local_model = base.local_model
        reasoning_effort = base.reasoning_effort
        if provider == "openrouter":
            if not base.openrouter_api_key:
                st.warning(
                    "No OPENROUTER_API_KEY is set. Use Demo, or add the key to "
                    "Streamlit secrets / your local `.env`."
                )
            selected_model = (
                base.model if base.model in COURSE_MODELS else COURSE_MODELS[0]
            )
            model = st.selectbox(
                "OpenRouter model",
                COURSE_MODELS,
                index=MODEL_INDEX[selected_model],
                key="openrouter_model",
            )
            reasoning_choice = st.selectbox(
                "Reasoning effort",
                ("none",) + ALLOWED_REASONING_EFFORTS,
                index=(
                    0
                    if not base.reasoning_effort
                    else ALLOWED_REASONING_EFFORTS.index(base.reasoning_effort)
                    + 1
                ),
                key="reasoning_effort",
            )
            reasoning_effort = (
                None if reasoning_choice == "none" else reasoning_choice
            )
        elif provider == "local":
            local_model = st.text_input(
                "Local model",
                value=base.local_model,
                placeholder="blank = auto-detect from /v1/models",
                key="local_model",
            )
            st.caption("Local endpoint: `http://127.0.0.1:21464/v1`")
        else:
            st.caption("Deterministic fixtures. No network, no key, no cost.")
            model = "demo/interview-coach"

        technique = st.selectbox(
            "Prompt technique",
            TECHNIQUE_ORDER,
            index=TECHNIQUE_ORDER.index(DEFAULT_TECHNIQUE),
            format_func=lambda key: TECHNIQUES[key].label,
            key="technique",
        )
        st.caption(TECHNIQUES[technique].description)

        temperature = st.slider(
            "Temperature",
            0.0,
            2.0,
            float(base.temperature),
            0.1,
            key="temperature",
        )
        max_token_limit = max(64, int(base.max_output_tokens))
        max_tokens = st.slider(
            "Max output tokens",
            32,
            max_token_limit,
            min(int(base.max_tokens), max_token_limit),
            16,
            key="max_tokens",
        )
        top_p = st.slider(
            "Top-p",
            0.0,
            1.0,
            float(base.top_p),
            0.05,
            key="top_p",
        )

        strict_safety = st.toggle(
            "Strict safety",
            value=base.strict_safety,
            help="Block injection patterns instead of warning and continuing.",
            key="strict_safety",
        )
        lexical_rag = st.toggle(
            "Lexical RAG-lite",
            value=base.enable_lexical_rag,
            help="Select relevant job-description chunks instead of the whole text.",
            key="lexical_rag",
        )

    st.sidebar.divider()
    st.sidebar.caption(
        f"Session budget: {base.max_calls} calls, "
        f"${base.session_cost_cap_usd:.2f} cap. "
        f"Inputs are capped at {base.max_input_chars:,} characters."
    )
    if st.sidebar.button("Clear session", use_container_width=True, key="clear"):
        session.reset()
        for key in ("q_result", "e_result", "chat_warnings"):
            st.session_state.pop(key, None)
        st.rerun()

    settings = replace(
        base,
        provider=provider,
        model=model,
        local_model=local_model,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        reasoning_effort=reasoning_effort,
        strict_safety=strict_safety,
        enable_lexical_rag=lexical_rag,
    )
    return settings, technique


def _show_stats(session: SessionState, settings: Settings) -> None:
    st.sidebar.metric("Calls", f"{session.calls}/{settings.max_calls}")
    st.sidebar.metric("Session cost", format_usd(session.cost_usd))
    if session.last_cost_source:
        st.sidebar.caption(f"Last call cost: {session.last_cost_source}")
    if session.calls and session.cost_usd >= settings.session_cost_cap_usd > 0:
        st.sidebar.error("Session cost cap reached; further model calls are blocked.")


def _prepare_tab(engine: InterviewEngine, technique: str) -> None:
    st.subheader("Prepare")
    role = st.text_input(
        "Target role",
        value=st.session_state.get("role", "AI engineer"),
        key="role_input",
    )
    job_description = st.text_area(
        "Job description (optional)",
        value=st.session_state.get("job_description", ""),
        height=180,
        placeholder="Paste the role description here. It is treated as data.",
        key="job_description_input",
    )
    col_a, col_b = st.columns(2)
    with col_a:
        difficulty = st.selectbox(
            "Difficulty",
            ("easy", "medium", "hard"),
            index=1,
            key="difficulty",
        )
    with col_b:
        count = st.slider("Questions", 3, 8, 5, key="question_count")

    if st.button("Generate question set", type="primary", key="generate"):
        st.session_state["role"] = role
        st.session_state["job_description"] = job_description
        try:
            result = engine.generate_questions(
                role=role,
                job_description=job_description,
                difficulty=difficulty,
                count=count,
                technique=technique,
            )
        except EngineError as exc:
            st.error(str(exc))
        else:
            st.session_state["q_result"] = result
            _session().questions = result.question_set
            st.session_state.pop("e_result", None)

    result = st.session_state.get("q_result")
    if not isinstance(result, QuestionGenerationResult):
        st.info("Choose a role and generate a question set to begin.")
        return
    if result.notice:
        st.caption(result.notice)
    _warnings(result.warnings)
    st.caption(f"Technique: {TECHNIQUES[result.technique].label}")
    for question in result.question_set.questions:
        with st.container(border=True):
            st.markdown(f"**{question.id}. {question.question}**")
            st.caption(f"{question.category} · {question.difficulty}")
            st.write(question.why)
            st.markdown("**Answer points:** " + "; ".join(question.answer_points))
    with st.expander("Raw QuestionSet JSON"):
        st.json(result.question_set.to_dict())


def _practice_tab(engine: InterviewEngine, technique: str) -> None:
    st.subheader("Practice")
    result = st.session_state.get("q_result")
    if not isinstance(result, QuestionGenerationResult):
        st.info("Generate a question set in the Prepare tab first.")
        return
    options = {
        f"{question.id}: {question.question}": question
        for question in result.question_set.questions
    }
    selected_label = st.selectbox("Question", list(options), key="practice_question")
    selected = options[selected_label]
    answer = st.text_area(
        "Your answer",
        height=180,
        placeholder="Write the answer you would give in the interview.",
        key="answer_input",
    )
    if st.button("Evaluate answer", type="primary", key="evaluate"):
        try:
            evaluation = engine.evaluate_answer(
                question=selected.question,
                answer=answer,
                job_description=st.session_state.get("job_description", ""),
                technique=technique,
            )
        except EngineError as exc:
            st.error(str(exc))
        else:
            st.session_state["e_result"] = evaluation
            _session().evaluation = evaluation.evaluation

    evaluation = st.session_state.get("e_result")
    if not isinstance(evaluation, EvaluationResult):
        return
    _warnings(evaluation.warnings)
    st.metric("Score", f"{evaluation.evaluation.score}/100")
    st.write(evaluation.evaluation.summary)
    left, right = st.columns(2)
    with left:
        st.markdown("**Strengths**")
        for item in evaluation.evaluation.strengths:
            st.write(f"- {item}")
    with right:
        st.markdown("**Gaps**")
        for item in evaluation.evaluation.gaps:
            st.write(f"- {item}")
    st.markdown("**Improved answer**")
    st.write(evaluation.evaluation.improved_answer)
    st.markdown("**Next steps**")
    for item in evaluation.evaluation.next_steps:
        st.write(f"- {item}")
    with st.expander("Raw AnswerEvaluation JSON"):
        st.json(evaluation.evaluation.to_dict())


def _coach_tab(engine: InterviewEngine, technique: str) -> None:
    st.subheader("Coach")
    st.caption("Multi-turn practice. History is kept only in this browser session.")
    session = _session()
    for message in session.messages:
        with st.chat_message(message.role):
            st.markdown(message.content)

    prompt = st.chat_input("Ask a follow-up question…")
    if prompt:
        history = list(session.messages)
        try:
            result = engine.chat(
                user_message=prompt,
                history=history,
                job_description=st.session_state.get("job_description", ""),
                technique=technique,
            )
        except EngineError as exc:
            st.error(str(exc))
        else:
            session.add_message("user", prompt)
            session.add_message("assistant", result.reply)
            st.session_state["chat_warnings"] = result.warnings
            st.rerun()

    warnings = st.session_state.get("chat_warnings")
    if warnings:
        _warnings(tuple(warnings))

    export = _export_markdown(session)
    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            "Export chat (Markdown)",
            data=export,
            file_name="interview-practice-chat.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_b:
        st.download_button(
            "Export chat (JSON)",
            data=_export_json(session),
            file_name="interview-practice-chat.json",
            mime="application/json",
            use_container_width=True,
        )


def _warnings(warnings: tuple[str, ...]) -> None:
    for warning in warnings:
        st.warning(warning)


def _export_markdown(session: SessionState) -> str:
    lines = ["# Interview Practice Coach", "", "Session-only chat export.", ""]
    if session.questions is not None:
        lines.extend(["## Question set", "", session.questions.role, ""])
        for question in session.questions.questions:
            lines.append(f"### {question.id}. {question.question}")
            lines.append(f"- Category: {question.category}")
            lines.append(f"- Difficulty: {question.difficulty}")
            lines.append(f"- Why: {question.why}")
            lines.append("- Answer points: " + "; ".join(question.answer_points))
            lines.append("")
    for message in session.messages:
        lines.append(f"**{message.role}:** {message.content}")
        lines.append("")
    return "\n".join(lines)


def _export_json(session: SessionState) -> str:
    import json

    payload = {
        "questions": (
            session.questions.to_dict() if session.questions is not None else None
        ),
        "evaluation": (
            session.evaluation.to_dict()
            if session.evaluation is not None
            else None
        ),
        "messages": [
            {"role": message.role, "content": message.content}
            for message in session.messages
        ],
    }
    return json.dumps(payload, indent=2)
