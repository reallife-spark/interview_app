from interview_practice.config import (
    COURSE_MODELS,
    DEFAULT_MODEL,
    Settings,
    apply_secret_values,
)

ENV_NAMES = (
    "PROVIDER",
    "OPENROUTER_API_KEY",
    "OPENROUTER_MODEL",
    "TEMPERATURE",
    "MAX_OUTPUT_TOKENS",
    "TOP_P",
    "REASONING_EFFORT",
    "STRICT_SAFETY",
    "ENABLE_LEXICAL_RAG",
    "MAX_CALLS",
    "MAX_INPUT_CHARS",
    "SESSION_COST_CAP_USD",
    "LOCAL_BASE_URL",
    "LOCAL_API_KEY",
    "LOCAL_MODEL",
)


def _clear(monkeypatch) -> None:
    for name in ENV_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_defaults_to_demo_without_key(monkeypatch) -> None:
    _clear(monkeypatch)
    settings = Settings.from_env(load_env_file=False)
    assert settings.provider == "demo"
    assert settings.model == DEFAULT_MODEL
    settings.validate()


def test_key_selects_openrouter(monkeypatch) -> None:
    _clear(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    settings = Settings.from_env(load_env_file=False)
    assert settings.provider == "openrouter"
    assert settings.has_openrouter_key
    settings.validate()


def test_redacted_hides_keys() -> None:
    settings = Settings(
        provider="openrouter",
        openrouter_api_key="secret-openrouter",
        local_api_key="secret-local",
    )
    redacted = settings.redacted()
    assert redacted["openrouter_api_key"] == "***"
    assert redacted["local_api_key"] == "***"
    assert "secret-openrouter" not in repr(redacted)
    assert "secret-local" not in repr(redacted)


def test_openrouter_rejects_non_course_model(monkeypatch) -> None:
    _clear(monkeypatch)
    settings = Settings(
        provider="openrouter",
        model="some/other-model",
        openrouter_api_key="test-key",
    )
    try:
        settings.validate()
    except ValueError as exc:
        assert "must be one of" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_course_models_are_the_three_expected_ids() -> None:
    assert COURSE_MODELS == (
        "openai/gpt-6-luna",
        "anthropic/claude-sonnet-5.5",
        "openai/gpt-6.1-sol",
    )


def test_streamlit_secret_enables_openrouter() -> None:
    base = Settings(provider="demo")
    settings = apply_secret_values(
        base,
        {
            "OPENROUTER_API_KEY": "secret-openrouter",
            "OPENROUTER_MODEL": "anthropic/claude-sonnet-5.5",
        },
    )
    assert settings.provider == "openrouter"
    assert settings.openrouter_api_key == "secret-openrouter"
    assert settings.model == "anthropic/claude-sonnet-5.5"
    assert "secret-openrouter" not in repr(settings)
    settings.validate()


def test_streamlit_secret_does_not_override_local_provider() -> None:
    base = Settings(
        provider="local",
        local_base_url="http://127.0.0.1:21464/v1",
    )
    settings = apply_secret_values(base, {"OPENROUTER_API_KEY": "secret-openrouter"})
    assert settings.provider == "local"
    assert settings.openrouter_api_key == "secret-openrouter"


def test_streamlit_numeric_and_boolean_secrets_are_applied() -> None:
    base = Settings(provider="demo")
    settings = apply_secret_values(
        base,
        {
            "MAX_CALLS": "7",
            "MAX_OUTPUT_TOKENS": "900",
            "SESSION_COST_CAP_USD": "1.25",
            "STRICT_SAFETY": "true",
            "OPENROUTER_APP_URL": "https://example.test/app",
        },
    )
    assert settings.max_calls == 7
    assert settings.max_output_tokens == 900
    assert settings.max_tokens == 900
    assert settings.session_cost_cap_usd == 1.25
    assert settings.strict_safety is True
    assert settings.openrouter_app_url == "https://example.test/app"


def test_settings_reject_invalid_caps() -> None:
    import pytest

    with pytest.raises(ValueError, match="max_calls"):
        Settings(max_calls=0).validate()
    with pytest.raises(ValueError, match="session_cost_cap_usd"):
        Settings(session_cost_cap_usd=-1).validate()


def test_model_options_cover_demo_openrouter_and_local() -> None:
    from interview_practice.config import (
        apply_model_selection,
        model_options,
        selection_for_settings,
    )

    options = model_options(["qwen3.6-35b-262k-q8"], configured_local_model="")
    assert options[0].key == "demo"
    assert any(option.provider == "openrouter" for option in options)
    assert any(option.key == "local:qwen3.6-35b-262k-q8" for option in options)
    selected = next(option for option in options if option.provider == "local")
    settings = apply_model_selection(Settings(provider="demo"), selected)
    assert settings.provider == "local"
    assert settings.local_model == "qwen3.6-35b-262k-q8"
    assert selection_for_settings(settings) == "local:qwen3.6-35b-262k-q8"


def test_model_selection_is_explicit() -> None:
    from interview_practice.config import ModelSelection, apply_model_selection

    settings = apply_model_selection(
        Settings(provider="local", local_model="old"),
        ModelSelection(
            key="openrouter:openai/gpt-6-luna",
            label="OpenRouter - openai/gpt-6-luna",
            provider="openrouter",
            model="openai/gpt-6-luna",
        ),
    )
    assert settings.provider == "openrouter"
    assert settings.model == "openai/gpt-6-luna"
    assert settings.local_model == ""
