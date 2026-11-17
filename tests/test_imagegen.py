import base64

import pytest

from interview_practice.config import Settings
from interview_practice.imagegen import ImageGenerationError, generate_image


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.last = None

    def post(self, url, **kwargs):
        self.last = (url, kwargs)
        return self.response


def _settings(**overrides):
    return Settings(
        provider="openrouter",
        openrouter_api_key="test-key",
        enable_image_generation=True,
        **overrides,
    )


def test_image_response_decodes_to_bytes() -> None:
    raw = b"\x89PNG\r\n\x1a\nfake"
    encoded = base64.b64encode(raw).decode()
    response = FakeResponse(
        {
            "model": "google/gemini-3.1-flash-image",
            "choices": [
                {
                    "message": {
                        "images": [
                            {"image_url": {"url": f"data:image/png;base64,{encoded}"}}
                        ]
                    }
                }
            ],
        }
    )
    session = FakeSession(response)
    result = generate_image(_settings(), "A calm study desk", session=session)
    assert result.data == raw
    assert result.mime_type == "image/png"
    assert session.last[1]["json"]["modalities"] == ["image", "text"]


def test_image_generation_is_hidden_for_demo_and_local() -> None:
    with pytest.raises(ImageGenerationError, match="only with OpenRouter"):
        generate_image(Settings(provider="demo", enable_image_generation=True), "x")
    with pytest.raises(ImageGenerationError, match="only with OpenRouter"):
        generate_image(Settings(provider="local", enable_image_generation=True), "x")


def test_image_generation_must_be_opted_in() -> None:
    with pytest.raises(ImageGenerationError, match="Enable image generation"):
        generate_image(
            Settings(provider="openrouter", openrouter_api_key="test-key"),
            "x",
        )
