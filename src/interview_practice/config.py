"""Configuration and course-level constants.

Environment variables are read here, never printed. The API keys are stored
with ``repr=False`` so an accidental dataclass dump does not leak them.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Literal

ProviderName = Literal["demo", "openrouter", "local"]

COURSE_MODELS: tuple[str, ...] = (
    "openai/gpt-6-luna",
    "anthropic/claude-sonnet-5.5",
    "openai/gpt-6.1-sol",
)
DEFAULT_MODEL = COURSE_MODELS[0]
COURSE_EMBEDDING_MODELS: tuple[str, ...] = (
    "qwen/qwen3-embedding-8b",
    "openai/text-embedding-3-small",
    "openai/text-embedding-3-large",
)
ALLOWED_REASONING_EFFORTS: tuple[str, ...] = ("low", "medium", "high")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LOCAL_BASE_URL = "http://127.0.0.1:21464/v1"
APP_URL = "https://real-life.dev"
APP_NAME = "Interview Practice Coach"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _load_env_file() -> None:
    """Load a local .env if python-dotenv is available.

    Values are never printed. Tests can bypass this with
    ``Settings.from_env(load_env_file=False)``.
    """

    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    project_env = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(dotenv_path=project_env, override=False)


def _default_provider(has_openrouter_key: bool) -> ProviderName:
    raw = os.getenv("PROVIDER", "").strip().lower()
    if raw in {"demo", "openrouter", "local"}:
        return raw  # type: ignore[return-value]
    return "openrouter" if has_openrouter_key else "demo"


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings for one session.

    ``openrouter_api_key`` and ``local_api_key`` are deliberately excluded
    from ``repr`` and from :meth:`redacted`.
    """

    provider: ProviderName = "demo"
    model: str = DEFAULT_MODEL
    temperature: float = 0.7
    max_tokens: int = 1200
    top_p: float = 1.0
    reasoning_effort: str | None = None
    strict_safety: bool = False
    enable_lexical_rag: bool = False
    max_calls: int = 20
    max_output_tokens: int = 1200
    max_input_chars: int = 8000
    session_cost_cap_usd: float = 0.50
    openrouter_api_key: str = field(default="", repr=False)
    local_base_url: str = LOCAL_BASE_URL
    local_api_key: str = field(default="", repr=False)
    local_model: str = ""

    @classmethod
    def from_env(cls, *, load_env_file: bool = True) -> Settings:
        if load_env_file:
            _load_env_file()
        openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
        provider = _default_provider(bool(openrouter_key))
        reasoning = os.getenv("REASONING_EFFORT", "").strip().lower() or None
        if reasoning not in ALLOWED_REASONING_EFFORTS:
            reasoning = None
        return cls(
            provider=provider,
            model=model,
            temperature=_env_float("TEMPERATURE", 0.7),
            max_tokens=_env_int("MAX_OUTPUT_TOKENS", 1200),
            top_p=_env_float("TOP_P", 1.0),
            reasoning_effort=reasoning,
            strict_safety=_env_bool("STRICT_SAFETY", False),
            enable_lexical_rag=_env_bool("ENABLE_LEXICAL_RAG", False),
            max_calls=_env_int("MAX_CALLS", 20),
            max_output_tokens=_env_int("MAX_OUTPUT_TOKENS", 1200),
            max_input_chars=_env_int("MAX_INPUT_CHARS", 8000),
            session_cost_cap_usd=_env_float("SESSION_COST_CAP_USD", 0.50),
            openrouter_api_key=openrouter_key,
            local_base_url=os.getenv("LOCAL_BASE_URL", LOCAL_BASE_URL).strip()
            or LOCAL_BASE_URL,
            local_api_key=os.getenv("LOCAL_API_KEY", "").strip(),
            local_model=os.getenv("LOCAL_MODEL", "").strip(),
        )

    def validate(self) -> None:
        if self.provider == "openrouter":
            if not self.openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY is required for OpenRouter mode")
            if self.model not in COURSE_MODELS:
                raise ValueError(
                    f"OpenRouter model must be one of {', '.join(COURSE_MODELS)}"
                )
        if self.provider == "local" and not self.local_base_url:
            raise ValueError("LOCAL_BASE_URL is required for local mode")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0 and 2")
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError("top_p must be between 0 and 1")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if self.max_calls <= 0:
            raise ValueError("max_calls must be positive")

    def redacted(self) -> dict[str, object]:
        data = asdict(self)
        data["openrouter_api_key"] = "***" if self.openrouter_api_key else ""
        data["local_api_key"] = "***" if self.local_api_key else ""
        return data

    @property
    def has_openrouter_key(self) -> bool:
        return bool(self.openrouter_api_key)


def apply_secret_values(
    settings: Settings,
    values: Mapping[str, object],
) -> Settings:
    """Merge Streamlit secrets without exposing them in the UI.

    Streamlit Cloud exposes secrets through ``st.secrets``, not reliably through
    ``os.environ``. The UI passes the secret mapping here; the core stays
    framework-independent and the key remains ``repr=False``.
    """

    updates: dict[str, object] = {}
    key = values.get("OPENROUTER_API_KEY")
    if isinstance(key, str) and key.strip():
        updates["openrouter_api_key"] = key.strip()
        if settings.provider == "demo":
            updates["provider"] = "openrouter"
    model = values.get("OPENROUTER_MODEL")
    if isinstance(model, str) and model.strip():
        updates["model"] = model.strip()
    local_key = values.get("LOCAL_API_KEY")
    if isinstance(local_key, str) and local_key.strip():
        updates["local_api_key"] = local_key.strip()
    local_model = values.get("LOCAL_MODEL")
    if isinstance(local_model, str) and local_model.strip():
        updates["local_model"] = local_model.strip()
    return replace(settings, **updates)
