"""Provider factory with explicit selection and no silent fallback."""

from __future__ import annotations

from interview_practice.config import ProviderName, Settings
from interview_practice.providers.base import (
    ChatMessage,
    Completion,
    Provider,
    ProviderError,
)
from interview_practice.providers.demo import DEMO_MODEL, DemoProvider
from interview_practice.providers.local import OpenAILocalProvider
from interview_practice.providers.openrouter import OpenRouterProvider

PROVIDER_NAMES: tuple[ProviderName, ...] = ("demo", "openrouter", "local")


def build_provider(settings: Settings) -> Provider:
    """Return the explicitly selected provider.

    A failure in local mode never falls back to OpenRouter: a private job
    description must not leave the machine because a tunnel is down.
    """

    if settings.provider == "openrouter":
        return OpenRouterProvider(settings.openrouter_api_key)
    if settings.provider == "local":
        return OpenAILocalProvider(
            settings.local_base_url,
            api_key=settings.local_api_key,
            default_model=settings.local_model,
        )
    if settings.provider == "demo":
        return DemoProvider()
    raise ProviderError(f"Unknown provider: {settings.provider}")


__all__ = [
    "ChatMessage",
    "Completion",
    "DEMO_MODEL",
    "DemoProvider",
    "OpenAILocalProvider",
    "OpenRouterProvider",
    "PROVIDER_NAMES",
    "Provider",
    "ProviderError",
    "build_provider",
]
