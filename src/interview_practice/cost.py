"""OpenRouter model metadata and cost estimates.

Prices are per token in the OpenRouter payload; the UI and this module use
per-million-token values. Unknown prices stay ``None`` rather than becoming a
fabricated number.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from interview_practice.config import COURSE_MODELS, OPENROUTER_BASE_URL


class CatalogError(RuntimeError):
    """The OpenRouter model catalog could not be fetched or parsed."""


@dataclass(frozen=True, slots=True)
class ModelInfo:
    id: str
    name: str = ""
    context_length: int | None = None
    prompt_per_million: float | None = None
    completion_per_million: float | None = None
    supported_parameters: tuple[str, ...] = ()

    @property
    def has_price(self) -> bool:
        return (
            self.prompt_per_million is not None
            and self.completion_per_million is not None
        )

    def supports(self, parameter: str) -> bool:
        return parameter in self.supported_parameters

    @property
    def supports_json_mode(self) -> bool:
        return self.supports("response_format")


@dataclass(frozen=True, slots=True)
class ModelCatalog:
    models: Mapping[str, ModelInfo] = field(default_factory=dict)
    fetched_at: str = ""

    @classmethod
    def from_payload(
        cls, payload: Mapping[str, Any], *, fetched_at: str = ""
    ) -> ModelCatalog:
        models: dict[str, ModelInfo] = {}
        for item in payload.get("data", []):
            if not isinstance(item, dict):
                continue
            model_id = item.get("id")
            if not isinstance(model_id, str) or not model_id:
                continue
            pricing = item.get("pricing") or {}
            prompt = _per_million(
                pricing.get("prompt") if isinstance(pricing, dict) else None
            )
            completion = _per_million(
                pricing.get("completion") if isinstance(pricing, dict) else None
            )
            context = item.get("context_length")
            context_length = context if isinstance(context, int) else None
            supported = item.get("supported_parameters") or []
            supported_parameters = tuple(
                value for value in supported if isinstance(value, str)
            )
            models[model_id] = ModelInfo(
                id=model_id,
                name=str(item.get("name") or model_id),
                context_length=context_length,
                prompt_per_million=prompt,
                completion_per_million=completion,
                supported_parameters=supported_parameters,
            )
        return cls(models=models, fetched_at=fetched_at)

    def get(self, model_id: str) -> ModelInfo | None:
        return self.models.get(model_id)

    def for_course_models(self) -> list[ModelInfo]:
        result = []
        for model_id in COURSE_MODELS:
            result.append(
                self.models.get(model_id)
                or ModelInfo(id=model_id, name=model_id)
            )
        return result


def default_catalog() -> ModelCatalog:
    """A price-less catalog so the UI can render before a network fetch."""
    return ModelCatalog(
        models={
            model_id: ModelInfo(id=model_id, name=model_id)
            for model_id in COURSE_MODELS
        }
    )


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: ModelInfo | None,
) -> float | None:
    if model is None or not model.has_price:
        return None
    prompt_price = model.prompt_per_million or 0.0
    completion_price = model.completion_per_million or 0.0
    return (prompt_tokens / 1_000_000) * prompt_price + (
        completion_tokens / 1_000_000
    ) * completion_price


def format_usd(amount: float | None) -> str:
    if amount is None:
        return "unavailable"
    if amount == 0:
        return "$0.00"
    if amount < 0.01:
        return f"${amount:.6f}"
    return f"${amount:.4f}"


def fetch_model_catalog(
    *,
    base_url: str = OPENROUTER_BASE_URL,
    api_key: str = "",
    timeout: float = 15.0,
) -> ModelCatalog:
    import requests

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = requests.get(
            f"{base_url.rstrip('/')}/models",
            headers=headers,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise CatalogError("Could not reach the OpenRouter model catalog") from exc
    if response.status_code >= 400:
        raise CatalogError(
            f"OpenRouter model catalog request failed ({response.status_code})"
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise CatalogError("OpenRouter model catalog returned invalid JSON") from exc
    return ModelCatalog.from_payload(payload, fetched_at="live")


def _per_million(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number < 0:
        return None
    return number * 1_000_000
