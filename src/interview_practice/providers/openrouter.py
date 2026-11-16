"""OpenRouter chat-completions provider."""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import Any

import requests

from interview_practice.config import APP_NAME, APP_URL, OPENROUTER_BASE_URL
from interview_practice.providers.base import (
    ChatMessage,
    Completion,
    ProviderError,
)


class OpenRouterProvider:
    name = "openrouter"

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = OPENROUTER_BASE_URL,
        session: requests.Session | None = None,
        timeout: float = 60.0,
    ) -> None:
        if not api_key:
            raise ProviderError("OPENROUTER_API_KEY is required for OpenRouter mode")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._session = session or requests.Session()
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": APP_URL,
            "X-Title": APP_NAME,
        }

    def list_models(self) -> list[str]:
        try:
            response = self._session.get(
                f"{self._base_url}/models",
                headers=self._headers(),
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise ProviderError("Could not reach OpenRouter") from exc
        if response.status_code >= 400:
            raise ProviderError(
                f"OpenRouter models request failed ({response.status_code})"
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderError(
                "OpenRouter returned an invalid models response"
            ) from exc
        models = []
        for item in payload.get("data", []):
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                models.append(item["id"])
        return sorted(models)

    def complete(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        temperature: float,
        max_tokens: int,
        top_p: float,
        reasoning_effort: str | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> Completion:
        payload: dict[str, Any] = {
            "model": model,
            "messages": [message.as_dict() for message in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }
        if reasoning_effort:
            payload["reasoning"] = {"effort": reasoning_effort}
        if response_format:
            payload["response_format"] = response_format

        started = time.monotonic()
        try:
            response = self._session.post(
                f"{self._base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise ProviderError("Could not reach OpenRouter") from exc
        latency_ms = int((time.monotonic() - started) * 1000)

        if response.status_code >= 400:
            raise ProviderError(
                f"OpenRouter request failed ({response.status_code})"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderError("OpenRouter returned an invalid response") from exc

        choices = data.get("choices") or []
        if not choices:
            raise ProviderError("OpenRouter returned no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, list):
            text = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            )
        elif isinstance(content, str):
            text = content
        else:
            text = ""
        if not text.strip():
            raise ProviderError("OpenRouter returned an empty response")

        usage = data.get("usage") or {}
        prompt_tokens = _int_or_zero(usage.get("prompt_tokens"))
        completion_tokens = _int_or_zero(usage.get("completion_tokens"))
        total_tokens = _int_or_zero(usage.get("total_tokens")) or (
            prompt_tokens + completion_tokens
        )
        cost = usage.get("cost")
        cost_usd = float(cost) if isinstance(cost, (int, float)) else None

        return Completion(
            text=text,
            model=str(data.get("model") or model),
            provider=self.name,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            finish_reason=str(choices[0].get("finish_reason") or ""),
        )


def _int_or_zero(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 0
