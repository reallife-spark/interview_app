"""Single-page Streamlit layout.

The engine is deliberately separate from this module so the provider, prompt,
safety and budget behaviour can be tested without a browser.
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import streamlit as st

from interview_practice.config import (
    ALLOWED_REASONING_EFFORTS,
    Settings,
    apply_model_selection,
    apply_secret_values,
    model_options,
    selection_for_settings,
)
from interview_practice.cost import format_usd
from interview_practice.engine import (
    EngineError,
    EvaluationResult,
    InterviewEngine,
    QuestionGenerationResult,
    RubricResult,
)
from interview_practice.imagegen import ImageGenerationError, generate_image
from interview_practice.prompts import (
    DEFAULT_DOMAIN,
    DEFAULT_PERSONA,
    DEFAULT_STYLE,
    DEFAULT_TECHNIQUE,
    PERSONA_ORDER,
    TECHNIQUE_ORDER,
    domain_options,
    persona_options,
    style_options,
    technique_options,
)
from interview_practice.providers import discover_local_models
from interview_practice.reports import build_jailbreak_workbook, load_fixtures
from interview_practice.session import SessionState

TECHNIQUE_BY_KEY = {item.key: item for item in technique_options()}
PERSONA_BY_KEY = {item.key: item for item in persona_options()}
DOMAIN_BY_KEY = {item.key: item for item in domain_options()}
STYLE_BY_KEY = {item.key: item for item in style_options()}


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
        _ensure_catalog(engine, settings)
        _show_model_info(engine, settings)
        if st.sidebar.button("Refresh OpenRouter prices", use_container_width=True):
            if engine.refresh_catalog():
                st.session_state["catalog"] = engine.catalog
                st.session_state["catalog_attempted"] = True
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
    local_models = list(st.session_state.get("local_models", []))
    options = model_options(
        local_models,
        configured_local_model=base.local_model,
    )
    by_key = {option.key: option for option in options}
    current_key = selection_for_settings(base)
    if current_key not in by_key:
        current_key = "demo"

    with st.sidebar.expander("Developer settings", expanded=True):
        selected_key = st.selectbox(
            "Model",
            [option.key for option in options],
            index=[option.key for option in options].index(current_key),
            format_func=lambda key: by_key[key].label,
            key="model_selection",
        )
        selection = by_key[selected_key]
        settings = apply_model_selection(base, selection)

        st.caption(f"agx64 gateway: `{base.local_base_url}`")
        if st.button(
            "Discover agx64 models",
            key="discover_local_models",
            use_container_width=True,
        ):
            try:
                discovered = discover_local_models(base)
            except Exception as exc:
                st.warning(f"Could not discover agx64 models: {exc}")
            else:
                if discovered:
                    st.session_state["local_models"] = discovered
                    st.rerun()
                else:
                    st.warning("The agx64 gateway returned no models.")

        if selection.provider == "openrouter":
            if not base.openrouter_api_key:
                st.warning(
                    "No OPENROUTER_API_KEY is set. Use Demo, or add the key to "
                    "Streamlit secrets / your local `.env`."
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
        elif selection.provider == "local":
            reasoning_effort = None
        else:
            st.caption("Deterministic fixtures. No network, no key, no cost.")
            reasoning_effort = None

        technique = st.selectbox(
            "Prompt technique",
            TECHNIQUE_ORDER,
            index=TECHNIQUE_ORDER.index(DEFAULT_TECHNIQUE),
            format_func=lambda key: TECHNIQUE_BY_KEY[key].label,
            key="technique",
        )
        st.caption(TECHNIQUE_BY_KEY[technique].description)

        domain = st.selectbox(
            "Practice domain",
            [item.key for item in domain_options()],
            index=[item.key for item in domain_options()].index(
                base.domain_profile
                if base.domain_profile in DOMAIN_BY_KEY
                else DEFAULT_DOMAIN
            ),
            format_func=lambda key: DOMAIN_BY_KEY[key].label,
            key="domain_profile",
        )
        style = st.selectbox(
            "Response style",
            [item.key for item in style_options()],
            index=[item.key for item in style_options()].index(
                base.response_style
                if base.response_style in STYLE_BY_KEY
                else DEFAULT_STYLE
            ),
            format_func=lambda key: STYLE_BY_KEY[key].label,
            key="response_style",
        )
        st.caption(STYLE_BY_KEY[style].instruction)

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
        question_memory = st.toggle(
            "Question memory (Chroma)",
            value=base.enable_question_memory,
            help="Check generated questions for near-duplicates using a vector store.",
            key="question_memory",
        )
        image_generation = st.toggle(
            "Image generation (OpenRouter only)",
            value=bool(base.enable_image_generation)
            and selection.provider == "openrouter",
            disabled=selection.provider != "openrouter",
            key="image_generation",
        )
        llm_judge = st.toggle(
            "LLM judge",
            value=base.enable_llm_judge,
            help="Add a second, opt-in judgement of the answer. Extra cost.",
            key="llm_judge",
        )
        chain_runtime = st.selectbox(
            "Chain runtime",
            ("native", "langchain"),
            index=0 if base.chain_runtime == "native" else 1,
            key="chain_runtime",
        )
        if st.button("Build jailbreak report", key="build_report"):
            fixtures_path = (
                Path(__file__).resolve().parents[4]
                / "tests"
                / "fixtures"
                / "red_team.json"
            )
            st.session_state["report_bytes"] = build_jailbreak_workbook(
                load_fixtures(fixtures_path)
            )
        report_bytes = st.session_state.get("report_bytes")
        if report_bytes:
            st.download_button(
                "Download jailbreak report (XLSX)",
                data=report_bytes,
                file_name="interview-practice-jailbreak.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
            )

    st.sidebar.divider()
    st.sidebar.caption(
        f"Session budget: {base.max_calls} calls, "
        f"${base.session_cost_cap_usd:.2f} cap. "
        f"Inputs are capped at {base.max_input_chars:,} characters."
    )
    if st.sidebar.button("Clear session", use_container_width=True, key="clear"):
        session.reset()
        for key in (
            "q_result",
            "e_result",
            "chat_warnings",
            "rubric_result",
            "judge_result",
            "image_result",
            "report_bytes",
        ):
            st.session_state.pop(key, None)
        st.rerun()

    settings = replace(
        settings,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        reasoning_effort=reasoning_effort,
        strict_safety=strict_safety,
        enable_lexical_rag=lexical_rag,
        enable_question_memory=question_memory,
        enable_image_generation=image_generation,
        enable_llm_judge=llm_judge,
        chain_runtime=chain_runtime,
        domain_profile=domain,
        response_style=style,
    )
    return settings, technique


def _ensure_catalog(engine: InterviewEngine, settings: Settings) -> None:
    if not settings.openrouter_api_key:
        return
    if "catalog" in st.session_state or st.session_state.get("catalog_attempted"):
        return
    st.session_state["catalog_attempted"] = True
    with st.spinner("Loading OpenRouter model metadata…"):
        if engine.refresh_catalog():
            st.session_state["catalog"] = engine.catalog
        else:
            st.sidebar.warning(
                "Could not load OpenRouter prices/capabilities; using safe defaults."
            )


def _show_model_info(engine: InterviewEngine, settings: Settings) -> None:
    info = engine.catalog.get(settings.model)
    if info is None:
        st.sidebar.caption("Model metadata is not loaded yet.")
        return
    context = (
        f"{info.context_length:,} tokens"
        if info.context_length
        else "context unknown"
    )
    if info.has_price:
        price = (
            f"in {format_usd(info.prompt_per_million)}/M · "
            f"out {format_usd(info.completion_per_million)}/M"
        )
    else:
        price = "price unavailable"
    st.sidebar.caption(f"{info.name}: {context} · {price}")
    json_mode = "yes" if info.supports_json_mode else "no/unknown"
    reasoning = "yes" if info.supports("reasoning") else "no/unknown"
    st.sidebar.caption(f"JSON mode: {json_mode} · Reasoning: {reasoning}")


def _show_stats(session: SessionState, settings: Settings) -> None:
    st.sidebar.metric("Calls", f"{session.calls}/{settings.max_calls}")
    st.sidebar.metric("Session cost", format_usd(session.cost_usd))
    usage = session.last_usage
    if usage is not None:
        st.sidebar.caption(
            f"Last: {usage.model} · {usage.prompt_tokens}/"
            f"{usage.completion_tokens} tokens · {usage.latency_ms} ms · "
            f"{format_usd(usage.cost_usd)} ({usage.cost_source})"
        )
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

    if st.button("Generate interview rubric", key="generate_rubric"):
        try:
            rubric_result = engine.generate_rubric(
                role=role,
                job_description=job_description,
            )
        except EngineError as exc:
            st.error(str(exc))
        else:
            st.session_state["rubric_result"] = rubric_result

    rubric_result = st.session_state.get("rubric_result")
    if isinstance(rubric_result, RubricResult):
        _warnings(rubric_result.warnings)
        st.markdown("**Interview rubric**")
        for criterion in rubric_result.rubric.criteria:
            st.markdown(
                f"- **{criterion.label}** ({criterion.weight}%): "
                + "; ".join(criterion.descriptors)
            )
        with st.expander("Raw InterviewRubric JSON"):
            st.json(rubric_result.rubric.to_dict())

    if (
        engine.settings.enable_image_generation
        and engine.settings.provider == "openrouter"
    ):
        st.divider()
        st.markdown("**Interview illustration (optional)**")
        image_prompt = st.text_input(
            "Image prompt",
            key="image_prompt",
            placeholder="A calm desk with notes and a laptop",
        )
        if st.button("Generate one image", key="generate_image"):
            try:
                image = generate_image(engine.settings, image_prompt)
            except ImageGenerationError as exc:
                st.error(str(exc))
            else:
                st.session_state["image_result"] = image
        image = st.session_state.get("image_result")
        if image is not None:
            st.image(image.data, caption=f"{image.model} · opt-in image call")

    result = st.session_state.get("q_result")
    if not isinstance(result, QuestionGenerationResult):
        st.info("Choose a role and generate a question set to begin.")
        return
    if result.notice:
        st.caption(result.notice)
    _warnings(result.warnings)
    st.caption(f"Technique: {TECHNIQUE_BY_KEY[result.technique].label}")
    if len(result.usages) > 1:
        st.caption(
            f"Chained calls: {len(result.usages)} · "
            f"total cost {format_usd(result.total_cost_usd)}"
        )
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
    persona = st.selectbox(
        "Interviewer style",
        PERSONA_ORDER,
        index=PERSONA_ORDER.index(DEFAULT_PERSONA),
        format_func=lambda key: PERSONA_BY_KEY[key].label,
        key="interviewer_persona",
    )
    st.caption(PERSONA_BY_KEY[persona].description)
    session = _session()
    for message in session.messages:
        with st.chat_message(message.role):
            st.markdown(message.content)

    prompt = st.chat_input("Ask a follow-up question…")
    if prompt:
        history = list(session.messages)
        current_evaluation = (
            json.dumps(session.evaluation.to_dict())
            if session.evaluation is not None
            else ""
        )
        try:
            result = engine.chat(
                user_message=prompt,
                history=history,
                job_description=st.session_state.get("job_description", ""),
                technique=technique,
                persona=persona,
                current_question=session.last_question,
                current_evaluation=current_evaluation,
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
