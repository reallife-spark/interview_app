"""Provider factory with explicit selection and no silent fallback."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from interview_practice.config import ProviderName, Settings
from interview_practice.providers._lib.demo import DemoProvider
from interview_practice.providers._lib.langchain import LangChainProvider
from interview_practice.providers._lib.local import OpenAILocalProvider
from interview_practice.providers._lib.openrouter import OpenRouterProvider
from interview_practice.providers.base import (
    Completion,
    CompletionRequest,
    Provider,
    ProviderError,
)

PROVIDER_NAMES: tuple[ProviderName, ...] = ("demo", "openrouter", "local")


def build_provider(
    settings: Settings,
    *,
    session: Any | None = None,
) -> Provider:
    """Return the explicitly selected provider.

    ``session`` is an injectable HTTP transport for adapter tests. A failure in
    local mode never falls back to OpenRouter: a private job description must
    not leave the machine because a tunnel is down.
    """

    if settings.chain_runtime == "langchain" and settings.provider != "openrouter":
        raise ProviderError("LangChain runtime requires OpenRouter mode.")
    if settings.provider == "openrouter":
        if settings.chain_runtime == "langchain":
            return LangChainProvider(settings)
        return OpenRouterProvider(
            settings.openrouter_api_key,
            session=session,
            app_url=settings.openrouter_app_url,
            timeout=settings.openrouter_timeout_seconds,
        )
    if settings.provider == "local":
        return OpenAILocalProvider(
            settings.local_base_url,
            api_key=settings.local_api_key,
            default_model=settings.local_model,
            session=session,
        )
    if settings.provider == "demo":
        return DemoProvider()
    raise ProviderError(f"Unknown provider: {settings.provider}")


def discover_local_models(
    settings: Settings, *, session: Any | None = None
) -> list[str]:
    """List agx64 models without changing the selected provider."""

    local = replace(settings, provider="local")
    return build_provider(local, session=session).list_models()


__all__ = [
    "Completion",
    "CompletionRequest",
    "PROVIDER_NAMES",
    "Provider",
    "ProviderError",
    "build_provider",
    "discover_local_models",
]
