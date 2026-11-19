"""OpenRouter chat-completions provider."""

from __future__ import annotations

import time
from typing import Any

import requests

from interview_practice.config import APP_NAME, APP_URL, OPENROUTER_BASE_URL
from interview_practice.providers._lib.http import (
    prefer_ipv4_session,
    request_with_retries,
)
from interview_practice.providers.base import (
    Completion,
    CompletionRequest,
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
        app_url: str = APP_URL,
    ) -> None:
        if not api_key:
            raise ProviderError("OPENROUTER_API_KEY is required for OpenRouter mode")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._session = session or prefer_ipv4_session()
        self._timeout = timeout
        self._app_url = app_url

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self._app_url,
            "X-Title": APP_NAME,
        }

    def list_models(self) -> list[str]:
        try:
            response = request_with_retries(
                self._session,
                "GET",
                f"{self._base_url}/models",
                headers=self._headers(),
                timeout=self._timeout,
                idempotent=True,
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

    def complete(self, request: CompletionRequest) -> Completion:
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": [message.as_dict() for message in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
        }
        if request.reasoning_effort:
            payload["reasoning"] = {"effort": request.reasoning_effort}
        if request.response_format:
            payload["response_format"] = request.response_format

        timeout = self._timeout
        retries = 2
        if request.reasoning_effort in {"medium", "high"}:
            timeout = max(self._timeout, 120.0)
            retries = 0 if request.reasoning_effort == "high" else 2
        return self._complete_once(
            request,
            payload,
            timeout=timeout,
            retries=retries,
        )

    def _complete_once(
        self,
        request: CompletionRequest,
        payload: dict[str, Any],
        *,
        timeout: float,
        retries: int,
        notice: str = "",
        allow_reasoning_fallback: bool = True,
    ) -> Completion:
        started = time.monotonic()
        try:
            response = request_with_retries(
                self._session,
                "POST",
                f"{self._base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=timeout,
                retries=retries,
            )
        except requests.Timeout as exc:
            raise ProviderError(
                f"OpenRouter timed out after {timeout:.0f}s"
            ) from exc
        except requests.RequestException as exc:
            raise ProviderError("Could not reach OpenRouter") from exc
        latency_ms = int((time.monotonic() - started) * 1000)

        if response.status_code >= 400:
            message = _safe_error_message(response)
            if (
                allow_reasoning_fallback
                and request.reasoning_effort
                and response.status_code in {400, 422}
                and _is_reasoning_error(message)
            ):
                fallback = dict(payload)
                fallback.pop("reasoning", None)
                return self._complete_once(
                    request,
                    fallback,
                    timeout=self._timeout,
                    retries=1,
                    notice=(
                        "The model did not support the selected reasoning "
                        "effort; the request was retried without reasoning."
                    ),
                    allow_reasoning_fallback=False,
                )
            suffix = f": {message}" if message else ""
            raise ProviderError(
                f"OpenRouter request failed ({response.status_code}){suffix}"
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
            finish_reason = str(choices[0].get("finish_reason") or "unknown")
            usage = data.get("usage") or {}
            completion_tokens = _int_or_zero(usage.get("completion_tokens"))
            reasoning_present = bool(
                message.get("reasoning") or message.get("reasoning_content")
            )
            hint = (
                " The model used the output budget on reasoning; raise Max "
                "output tokens or choose a non-reasoning or medium-reasoning "
                "model."
                if reasoning_present
                else " The model returned no visible content."
            )
            raise ProviderError(
                "OpenRouter returned empty content "
                f"(finish_reason={finish_reason}, "
                f"completion_tokens={completion_tokens})."
                + hint
            )

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
            model=str(data.get("model") or request.model),
            provider=self.name,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            finish_reason=str(choices[0].get("finish_reason") or ""),
            notice=notice,
        )


def _safe_error_message(response: Any) -> str:
    try:
        payload = response.json()
    except ValueError:
        return ""
    if not isinstance(payload, dict):
        return ""
    error = payload.get("error")
    if not isinstance(error, dict):
        return ""
    message = error.get("message")
    if not isinstance(message, str):
        return ""
    return " ".join(message.split())[:200]


def _is_reasoning_error(message: str) -> bool:
    lowered = message.lower()
    return "reason" in lowered or "effort" in lowered


def _int_or_zero(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 0
