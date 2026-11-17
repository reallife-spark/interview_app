from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[4] / "app.py"


def _button(at: AppTest, key: str):
    for button in at.button:
        if button.key == key:
            return button
    raise AssertionError(f"button not found: {key}")


def _demo_app(monkeypatch) -> AppTest:
    monkeypatch.setenv("PROVIDER", "demo")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    return at


def test_app_renders_in_demo_mode(monkeypatch) -> None:
    at = _demo_app(monkeypatch)
    assert at.title[0].value == "Interview Practice Coach"
    assert len(at.tabs) == 3
    assert any(item.value == "demo" for item in at.selectbox)


def test_model_selector_is_visible(monkeypatch) -> None:
    at = _demo_app(monkeypatch)
    selector = next(item for item in at.selectbox if item.key == "model_selection")
    assert any(value.startswith("Demo -") for value in selector.options)
    assert any(value.startswith("OpenRouter -") for value in selector.options)


def test_local_model_option_can_be_selected(monkeypatch) -> None:
    monkeypatch.setenv("PROVIDER", "demo")
    monkeypatch.setenv("LOCAL_MODEL", "qwen3.6-35b-262k-q8")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    selector = next(item for item in at.selectbox if item.key == "model_selection")
    assert any(value.startswith("agx64 - ") for value in selector.options)
    selector.select("local:qwen3.6-35b-262k-q8").run()
    assert not at.exception
    assert any(
        "agx64 gateway" in caption.value for caption in at.sidebar.caption
    )


def test_discover_local_models_without_configured_model(monkeypatch) -> None:
    monkeypatch.setenv("PROVIDER", "demo")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LOCAL_MODEL", raising=False)
    monkeypatch.setattr(
        "interview_practice.ui._lib.layout.discover_local_models",
        lambda settings: ["qwen3-vl-4b-65k:latest"],
    )
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception
    button = _button(at, "discover_local_models")
    button.click().run()
    assert not at.exception
    selector = next(item for item in at.selectbox if item.key == "model_selection")
    assert "agx64 - qwen3-vl-4b-65k:latest" in selector.options


def test_persona_selector_is_visible(monkeypatch) -> None:
    at = _demo_app(monkeypatch)
    assert any(item.key == "interviewer_persona" for item in at.selectbox)


def test_generate_questions_in_demo_mode(monkeypatch) -> None:
    at = _demo_app(monkeypatch)
    _button(at, "generate").click().run()
    assert not at.exception
    result = at.session_state["q_result"]
    assert result.question_set.questions
    assert "q1" in result.question_set.questions[0].id


def test_clear_session_resets_demo_state(monkeypatch) -> None:
    at = _demo_app(monkeypatch)
    _button(at, "generate").click().run()
    assert at.session_state["q_result"] is not None
    _button(at, "clear").click().run()
    assert "q_result" not in at.session_state


def _text_area(at: AppTest, key: str):
    for area in at.text_area:
        if area.key == key:
            return area
    raise AssertionError(f"text area not found: {key}")


def test_practice_evaluation_in_demo_mode(monkeypatch) -> None:
    at = _demo_app(monkeypatch)
    _button(at, "generate").click().run()
    _text_area(at, "answer_input").input(
        "I would use a labelled set, retrieval recall, groundedness and a "
        "release gate."
    ).run()
    _button(at, "evaluate").click().run()
    assert not at.exception
    result = at.session_state["e_result"]
    assert 0 <= result.evaluation.score <= 100
    assert result.evaluation.improved_answer


def test_generate_rubric_in_demo_mode(monkeypatch) -> None:
    at = _demo_app(monkeypatch)
    _button(at, "generate_rubric").click().run()
    assert not at.exception
    result = at.session_state["rubric_result"]
    assert len(result.rubric.criteria) == 4
    assert sum(item.weight for item in result.rubric.criteria) == 100
