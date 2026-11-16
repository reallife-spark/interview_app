from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"


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
