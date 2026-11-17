import json

import pytest

from interview_practice.config import Settings
from interview_practice.messages import ChatMessage
from interview_practice.providers import (
    CompletionRequest,
    ProviderError,
    build_provider,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, *, get_response=None, post_response=None):
        self.get_response = get_response
        self.post_response = post_response
        self.last_get = None
        self.last_post = None

    def get(self, url, **kwargs):
        self.last_get = (url, kwargs)
        if self.get_response is None:
            raise AssertionError("unexpected GET")
        return self.get_response

    def post(self, url, **kwargs):
        self.last_post = (url, kwargs)
        if self.post_response is None:
            raise AssertionError("unexpected POST")
        return self.post_response


def _request(**overrides) -> CompletionRequest:
    values = {
        "messages": (ChatMessage("user", "u"),),
        "model": "openai/gpt-6-luna",
        "temperature": 0.7,
        "max_tokens": 50,
        "top_p": 1.0,
    }
    values.update(overrides)
    return CompletionRequest(**values)


def _openrouter_settings() -> Settings:
    return Settings(provider="openrouter", openrouter_api_key="test-key")


def test_openrouter_requires_key() -> None:
    with pytest.raises(ProviderError, match="OPENROUTER_API_KEY"):
        build_provider(Settings(provider="openrouter", openrouter_api_key=""))


def test_openrouter_complete_shapes_request_and_parses_usage() -> None:
    response = FakeResponse(
        {
            "model": "openai/gpt-6-luna",
            "choices": [
                {
                    "message": {"content": "Hello"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 3,
                "total_tokens": 15,
                "cost": 0.0001,
            },
        }
    )
    session = FakeSession(post_response=response)
    provider = build_provider(_openrouter_settings(), session=session)
    completion = provider.complete(
        CompletionRequest(
            messages=(
                ChatMessage("system", "s"),
                ChatMessage("user", "u"),
            ),
            model="openai/gpt-6-luna",
            temperature=0.3,
            max_tokens=200,
            top_p=0.9,
            reasoning_effort="low",
            response_format={"type": "json_object"},
        )
    )
    assert completion.text == "Hello"
    assert completion.prompt_tokens == 12
    assert completion.completion_tokens == 3
    assert completion.cost_usd == 0.0001
    assert completion.finish_reason == "stop"
    url, kwargs = session.last_post
    assert url.endswith("/chat/completions")
    assert kwargs["headers"]["Authorization"] == "Bearer test-key"
    assert kwargs["json"]["model"] == "openai/gpt-6-luna"
    assert kwargs["json"]["messages"] == [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "u"},
    ]
    assert kwargs["json"]["reasoning"] == {"effort": "low"}
    assert kwargs["json"]["response_format"] == {"type": "json_object"}


def test_openrouter_http_error_is_safe() -> None:
    provider = build_provider(
        _openrouter_settings(),
        session=FakeSession(post_response=FakeResponse({}, status_code=429)),
    )
    with pytest.raises(ProviderError, match="429"):
        provider.complete(_request())


def test_openrouter_lists_models() -> None:
    provider = build_provider(
        _openrouter_settings(),
        session=FakeSession(
            get_response=FakeResponse({"data": [{"id": "b/model"}, {"id": "a/model"}]})
        ),
    )
    assert provider.list_models() == ["a/model", "b/model"]


def test_local_provider_autodetects_model_and_has_no_cost() -> None:
    session = FakeSession(
        get_response=FakeResponse({"data": [{"id": "qwen-local"}]}),
        post_response=FakeResponse(
            {
                "model": "qwen-local",
                "choices": [{"message": {"content": "local answer"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 2},
            }
        ),
    )
    provider = build_provider(
        Settings(
            provider="local",
            local_base_url="http://127.0.0.1:21464/v1",
        ),
        session=session,
    )
    assert provider.list_models() == ["qwen-local"]
    completion = provider.complete(_request(model=""))
    assert completion.text == "local answer"
    assert completion.cost_usd == 0.0
    assert session.last_post[1]["json"]["model"] == "qwen-local"


def test_local_provider_reports_thinking_model_token_cap() -> None:
    session = FakeSession(
        post_response=FakeResponse(
            {
                "model": "qwen3-vl-4b-65k:latest",
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "reasoning": "private reasoning must not be exposed",
                        },
                        "finish_reason": "length",
                    }
                ],
                "usage": {
                    "prompt_tokens": 323,
                    "completion_tokens": 1200,
                    "total_tokens": 1523,
                },
            }
        )
    )
    provider = build_provider(
        Settings(
            provider="local",
            local_base_url="http://127.0.0.1:21464/v1",
            local_model="qwen3-vl-4b-65k:latest",
        ),
        session=session,
    )
    with pytest.raises(ProviderError) as exc:
        provider.complete(_request(model="qwen3-vl-4b-65k:latest"))
    message = str(exc.value)
    assert "finish_reason=length" in message
    assert "completion_tokens=1200" in message
    assert "non-thinking" in message
    assert "private reasoning" not in message


def test_demo_provider_returns_question_json() -> None:
    provider = build_provider(Settings(provider="demo"))
    completion = provider.complete(
        _request(
            messages=(
                ChatMessage("user", "Generate a QuestionSet for an AI engineer"),
            )
        )
    )
    payload = json.loads(completion.text)
    assert payload["role"] == "AI engineer"
    assert len(payload["questions"]) == 3
    assert completion.cost_usd == 0.0


def test_demo_provider_returns_evaluation_json() -> None:
    provider = build_provider(Settings(provider="demo"))
    completion = provider.complete(
        _request(
            messages=(
                ChatMessage("user", "Evaluate this answer and return AnswerEvaluation"),
            )
        )
    )
    payload = json.loads(completion.text)
    assert 0 <= payload["score"] <= 100
    assert "improved_answer" in payload


def test_factory_does_not_fallback_from_local() -> None:
    settings = Settings(provider="local", local_base_url="")
    with pytest.raises(ProviderError, match="LOCAL_BASE_URL"):
        build_provider(settings)


def test_factory_returns_demo() -> None:
    provider = build_provider(Settings(provider="demo"))
    assert provider.name == "demo"
    assert provider.list_models() == ["demo/interview-coach"]


def test_openrouter_uses_configured_app_url() -> None:
    response = FakeResponse(
        {
            "model": "openai/gpt-6-luna",
            "choices": [{"message": {"content": "ok"}}],
            "usage": {},
        }
    )
    settings = Settings(
        provider="openrouter",
        openrouter_api_key="test-key",
        openrouter_app_url="https://example.test/app",
    )
    provider = build_provider(settings, session=FakeSession(post_response=response))
    provider.complete(_request())
    session = provider._session  # noqa: SLF001 - test inspects the injected transport
    assert session.last_post[1]["headers"]["HTTP-Referer"] == "https://example.test/app"
