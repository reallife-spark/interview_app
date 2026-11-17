"""Optional LangChain LCEL adapter for OpenRouter.

The package is optional. Selecting this runtime without the dependency must
fail clearly; it never falls back to the native adapter.
"""

from __future__ import annotations

import time
from typing import Any

from interview_practice.config import Settings
from interview_practice.messages import ChatMessage
from interview_practice.providers.base import (
    Completion,
    CompletionRequest,
    ProviderError,
)

try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:  # pragma: no cover - exercised only without the extra
    HumanMessage = SystemMessage = None  # type: ignore[assignment]


def _langchain_messages(messages: list[ChatMessage]) -> list[Any]:
    if HumanMessage is None or SystemMessage is None:
        raise ProviderError(
            "LangChain runtime selected but langchain-core is not installed."
        )
    mapped = []
    for message in messages:
        if message.role == "system":
            mapped.append(SystemMessage(content=message.content))
        else:
            mapped.append(HumanMessage(content=message.content))
    return mapped


class LangChainProvider:
    name = "openrouter-langchain"

    def __init__(self, settings: Settings) -> None:
        if settings.provider != "openrouter":
            raise ProviderError("LangChain runtime requires OpenRouter mode.")
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:  # pragma: no cover - optional extra
            raise ProviderError(
                "LangChain runtime selected but langchain-openai is not installed."
            ) from exc
        try:
            self._client = ChatOpenAI(
                model=settings.model,
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                top_p=settings.top_p,
                timeout=120,
                default_headers={
                    "HTTP-Referer": settings.openrouter_app_url,
                    "X-Title": "Interview Practice Coach",
                },
            )
        except Exception as exc:
            raise ProviderError(
                "Could not initialise the LangChain OpenRouter client."
            ) from exc

    def list_models(self) -> list[str]:
        raise ProviderError(
            "Model discovery is not available through the LangChain runtime."
        )

    def complete(self, request: CompletionRequest) -> Completion:
        started = time.monotonic()
        try:
            response = self._client.invoke(_langchain_messages(list(request.messages)))
        except Exception as exc:
            raise ProviderError(
                "The LangChain OpenRouter call failed."
            ) from exc
        latency_ms = int((time.monotonic() - started) * 1000)
        text = response.content
        if not isinstance(text, str) or not text.strip():
            raise ProviderError("The LangChain runtime returned an empty response.")
        usage = getattr(response, "usage_metadata", {}) or {}
        prompt_tokens = int(usage.get("input_tokens", 0) or 0)
        completion_tokens = int(usage.get("output_tokens", 0) or 0)
        total_tokens = int(usage.get("total_tokens", 0) or 0) or (
            prompt_tokens + completion_tokens
        )
        metadata = getattr(response, "response_metadata", {}) or {}
        return Completion(
            text=text,
            model=str(metadata.get("model_name") or request.model),
            provider=self.name,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=None,
            finish_reason=str(metadata.get("finish_reason") or ""),
        )
