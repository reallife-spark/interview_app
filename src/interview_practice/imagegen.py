"""Opt-in OpenRouter image generation.

Image generation is intentionally not part of the demo or `agx64` paths. It
costs money, is slower than text, and should never run unless the user asks for
one image in an explicit action.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from typing import Any

import requests

from interview_practice.config import DEFAULT_IMAGE_MODEL, Settings


class ImageGenerationError(RuntimeError):
    """A safe, user-facing image-generation failure."""


@dataclass(frozen=True, slots=True)
class ImageResult:
    data: bytes
    mime_type: str
    model: str
    prompt: str


def _data_url_bytes(value: object) -> tuple[bytes, str]:
    if not isinstance(value, str) or not value.startswith("data:"):
        raise ImageGenerationError("Image response did not contain a data URL.")
    header, _, encoded = value.partition(",")
    if ";base64" not in header or not encoded:
        raise ImageGenerationError("Image response was not base64 encoded.")
    mime = header[5:].split(";", 1)[0] or "image/png"
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ImageGenerationError("Image response was not valid base64.") from exc
    if not data or len(data) > 8 * 1024 * 1024:
        raise ImageGenerationError("Image response was empty or too large.")
    return data, mime


def generate_image(
    settings: Settings,
    prompt: str,
    *,
    session: requests.Session | None = None,
    timeout: float = 120.0,
) -> ImageResult:
    if settings.provider != "openrouter":
        raise ImageGenerationError(
            "Image generation is available only with OpenRouter."
        )
    if not settings.enable_image_generation:
        raise ImageGenerationError("Enable image generation in settings first.")
    text = prompt.strip()
    if not text:
        raise ImageGenerationError("Write an image prompt first.")
    if len(text) > 1000:
        raise ImageGenerationError("Image prompt must be at most 1,000 characters.")
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.openrouter_app_url,
        "X-Title": "Interview Practice Coach",
    }
    payload: dict[str, Any] = {
        "model": settings.image_model or DEFAULT_IMAGE_MODEL,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Create one clean, professional illustration for interview "
                    "preparation. Do not include text, logos or personal data. "
                    + text
                ),
            }
        ],
        "modalities": ["image", "text"],
        "max_tokens": 256,
    }
    client = session or requests.Session()
    try:
        response = client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise ImageGenerationError(
            "The image provider could not be reached."
        ) from exc
    if response.status_code >= 400:
        raise ImageGenerationError(
            f"Image provider returned HTTP {response.status_code}."
        )
    try:
        data = response.json()
    except ValueError as exc:
        raise ImageGenerationError("Image provider returned invalid JSON.") from exc
    images = (
        ((data.get("choices") or [{}])[0].get("message") or {}).get("images")
        if isinstance(data, dict)
        else None
    )
    if not isinstance(images, list) or not images:
        raise ImageGenerationError("Image provider returned no image.")
    first = images[0]
    url = first.get("image_url", {}).get("url") if isinstance(first, dict) else None
    raw, mime = _data_url_bytes(url)
    model = data.get("model") if isinstance(data, dict) else None
    return ImageResult(
        data=raw,
        mime_type=mime,
        model=str(model or settings.image_model),
        prompt=text,
    )
