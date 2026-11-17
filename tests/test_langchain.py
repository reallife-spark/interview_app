import pytest

pytest.importorskip("langchain_core")
pytest.importorskip("langchain_openai")

from interview_practice.config import Settings
from interview_practice.messages import ChatMessage
from interview_practice.providers import build_provider
from interview_practice.providers.base import CompletionRequest, ProviderError


class FakeResponse:
    content = "chain reply"
    usage_metadata = {
        "input_tokens": 3,
        "output_tokens": 2,
        "total_tokens": 5,
    }
    response_metadata = {"model_name": "fake/model", "finish_reason": "stop"}


class FakeClient:
    def __init__(self):
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return FakeResponse()


def test_langchain_runtime_is_explicitly_selected() -> None:
    settings = Settings(
        provider="openrouter",
        openrouter_api_key="test-key",
        chain_runtime="langchain",
    )
    provider = build_provider(settings)
    assert provider.name == "openrouter-langchain"


def test_langchain_runtime_requires_openrouter() -> None:
    with pytest.raises(ProviderError, match="requires OpenRouter"):
        build_provider(Settings(provider="demo", chain_runtime="langchain"))


def test_langchain_adapter_maps_messages_and_usage() -> None:
    settings = Settings(
        provider="openrouter",
        openrouter_api_key="test-key",
        chain_runtime="langchain",
    )
    provider = build_provider(settings)
    fake = FakeClient()
    provider._client = fake
    completion = provider.complete(
        CompletionRequest(
            messages=[
                ChatMessage("system", "rules"),
                ChatMessage("user", "hello"),
            ],
            model="openai/gpt-6-luna",
            temperature=0.2,
            max_tokens=100,
            top_p=1.0,
        )
    )
    assert completion.text == "chain reply"
    assert completion.total_tokens == 5
    assert len(fake.messages) == 2
