"""OpenAI-compatible local provider for the agx64 developer tunnel."""

from __future__ import annotations

import time
from typing import Any

import requests

from interview_practice.config import LOCAL_BASE_URL
from interview_practice.providers._lib.http import (
    prefer_ipv4_session,
    request_with_retries,
)
from interview_practice.providers.base import (
    Completion,
    CompletionRequest,
    ProviderError,
)


class OpenAILocalProvider:
    name = "local"

    def __init__(
        self,
        base_url: str = LOCAL_BASE_URL,
        *,
        api_key: str = "",
        default_model: str = "",
        session: requests.Session | None = None,
        timeout: float = 120.0,
    ) -> None:
        if not base_url:
            raise ProviderError("LOCAL_BASE_URL is required for local mode")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._default_model = default_model
        self._session = session or prefer_ipv4_session()
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def list_models(self) -> list[str]:
        try:
            response = request_with_retries(
                self._session,
                "GET",
                f"{self._base_url}/models",
                headers=self._headers(),
                timeout=10,
                idempotent=True,
            )
        except requests.RequestException as exc:
            raise ProviderError(
                "Could not reach the local model endpoint; is the agx64 tunnel up?"
            ) from exc
        if response.status_code >= 400:
            raise ProviderError(f"Local models request failed ({response.status_code})")
        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderError("Local endpoint returned invalid model JSON") from exc
        models = []
        for item in payload.get("data", []):
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                models.append(item["id"])
        return sorted(models)

    def complete(self, request: CompletionRequest) -> Completion:
        chosen_model = request.model or self._default_model
        if not chosen_model:
            available = self.list_models()
            if not available:
                raise ProviderError("The local endpoint reported no models")
            chosen_model = available[0]

        payload: dict[str, Any] = {
            "model": chosen_model,
            "messages": [message.as_dict() for message in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
        }
        if request.response_format:
            payload["response_format"] = request.response_format

        started = time.monotonic()
        try:
            response = request_with_retries(
                self._session,
                "POST",
                f"{self._base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise ProviderError(
                "Could not reach the local model endpoint; is the agx64 tunnel up?"
            ) from exc
        latency_ms = int((time.monotonic() - started) * 1000)

        if response.status_code >= 400:
            raise ProviderError(f"Local model request failed ({response.status_code})")
        try:
            data = response.json()
        except ValueError as exc:
            raise ProviderError(
                "Local endpoint returned invalid response JSON"
            ) from exc

        choices = data.get("choices") or []
        if not choices:
            raise ProviderError("Local endpoint returned no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        text = content if isinstance(content, str) else ""
        if not text.strip():
            raise ProviderError("Local endpoint returned an empty response")

        usage = data.get("usage") or {}
        prompt_tokens = _int_or_zero(usage.get("prompt_tokens"))
        completion_tokens = _int_or_zero(usage.get("completion_tokens"))
        total_tokens = _int_or_zero(usage.get("total_tokens")) or (
            prompt_tokens + completion_tokens
        )
        return Completion(
            text=text,
            model=str(data.get("model") or chosen_model),
            provider=self.name,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=0.0,
            finish_reason=str(choices[0].get("finish_reason") or ""),
        )


def _int_or_zero(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 0
