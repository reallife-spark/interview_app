"""Configuration and course-level constants.

Environment variables are read here, never printed. The API keys are stored
with ``repr=False`` so an accidental dataclass dump does not leak them.
"""

from __future__ import annotations

import os
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Literal

ProviderName = Literal["demo", "openrouter", "local"]
ChainRuntime = Literal["native", "langchain"]

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
ALLOWED_CHAIN_RUNTIMES: tuple[ChainRuntime, ...] = ("native", "langchain")
ALLOWED_RESPONSE_STYLES: tuple[str, ...] = ("balanced", "concise", "detailed")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LOCAL_BASE_URL = "http://127.0.0.1:21464/v1"
PUBLIC_APP_URL = "https://interviewap-nbsnftcgrwj7yjcm2h658m.streamlit.app/"
APP_URL = PUBLIC_APP_URL
APP_NAME = "Interview Practice Coach"
DEFAULT_IMAGE_MODEL = "google/gemini-3.1-flash-image"
DEFAULT_EMBEDDING_MODEL = COURSE_EMBEDDING_MODELS[0]
DEFAULT_LOCAL_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_DOMAIN = "ai_engineering"
DEFAULT_RESPONSE_STYLE = "balanced"


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


def _coerce_int(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _coerce_float(value: object, default: float) -> float:
    if isinstance(value, bool):
        return default
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _coerce_bool(value: object, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return default


def _coerce_choice(
    value: object,
    default: str,
    allowed: Sequence[str],
) -> str:
    if isinstance(value, str) and value.strip() in allowed:
        return value.strip()
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
class ModelSelection:
    """One option in the learner-facing model selector."""

    key: str
    label: str
    provider: ProviderName
    model: str
    local_model: str = ""


def model_options(
    local_models: Sequence[str] = (),
    *,
    configured_local_model: str = "",
    include_demo: bool = False,
) -> tuple[ModelSelection, ...]:
    """Build one deterministic selector from OpenRouter and agx64.

    Demo is a developer-only option and is included only when ``include_demo``
    is true (``PROVIDER=demo`` in the Streamlit UI).
    """

    options: list[ModelSelection] = []
    if include_demo:
        options.append(
            ModelSelection(
                key="demo",
                label="Demo - deterministic, no network",
                provider="demo",
                model="demo/interview-coach",
            )
        )
    for model in COURSE_MODELS:
        options.append(
            ModelSelection(
                key=f"openrouter:{model}",
                label=f"OpenRouter - {model}",
                provider="openrouter",
                model=model,
            )
        )
    discovered = sorted({value for value in local_models if value})
    if configured_local_model and configured_local_model not in discovered:
        discovered.insert(0, configured_local_model)
    for model in discovered:
        options.append(
            ModelSelection(
                key=f"local:{model}",
                label=f"agx64 - {model}",
                provider="local",
                model=model,
                local_model=model,
            )
        )
    return tuple(options)


def apply_model_selection(
    settings: Settings,
    selection: ModelSelection,
) -> Settings:
    return replace(
        settings,
        provider=selection.provider,
        model=selection.model,
        local_model=selection.local_model,
    )


def selection_for_settings(settings: Settings) -> str:
    if settings.provider == "demo":
        return "demo"
    if settings.provider == "local":
        return f"local:{settings.local_model}"
    return f"openrouter:{settings.model}"


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
    global_max_calls_per_day: int = 500
    global_max_cost_per_day: float = 5.00
    global_rate_per_minute: int = 30
    openrouter_api_key: str = field(default="", repr=False)
    openrouter_app_url: str = PUBLIC_APP_URL
    openrouter_timeout_seconds: float = 60.0
    local_base_url: str = LOCAL_BASE_URL
    local_api_key: str = field(default="", repr=False)
    local_model: str = ""
    local_uncapped_output: bool = True
    local_timeout_seconds: float = 330.0
    enable_question_memory: bool = False
    question_memory_path: str = ".chroma"
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    local_embedding_model: str = DEFAULT_LOCAL_EMBEDDING_MODEL
    question_memory_max_items: int = 500
    question_memory_duplicate_distance: float = 0.15
    enable_image_generation: bool = False
    image_model: str = DEFAULT_IMAGE_MODEL
    enable_llm_judge: bool = False
    chain_runtime: ChainRuntime = "native"
    domain_profile: str = DEFAULT_DOMAIN
    response_style: str = DEFAULT_RESPONSE_STYLE

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
        chain_runtime = _coerce_choice(
            os.getenv("CHAIN_RUNTIME", "native"),
            "native",
            ALLOWED_CHAIN_RUNTIMES,
        )
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
            global_max_calls_per_day=_env_int("GLOBAL_MAX_CALLS_PER_DAY", 500),
            global_max_cost_per_day=_env_float("GLOBAL_MAX_COST_PER_DAY", 5.00),
            global_rate_per_minute=_env_int("GLOBAL_RATE_PER_MINUTE", 30),
            openrouter_api_key=openrouter_key,
            openrouter_app_url=(
                os.getenv("OPENROUTER_APP_URL", PUBLIC_APP_URL).strip()
                or PUBLIC_APP_URL
            ),
            openrouter_timeout_seconds=_env_float(
                "OPENROUTER_TIMEOUT_SECONDS", 60.0
            ),
            local_base_url=os.getenv("LOCAL_BASE_URL", LOCAL_BASE_URL).strip()
            or LOCAL_BASE_URL,
            local_api_key=os.getenv("LOCAL_API_KEY", "").strip(),
            local_model=os.getenv("LOCAL_MODEL", "").strip(),
            local_uncapped_output=_env_bool("LOCAL_UNCAPPED_OUTPUT", True),
            local_timeout_seconds=_env_float("LOCAL_TIMEOUT_SECONDS", 330.0),
            enable_question_memory=_env_bool("ENABLE_QUESTION_MEMORY", False),
            question_memory_path=os.getenv(
                "QUESTION_MEMORY_PATH", ".chroma"
            ).strip()
            or ".chroma",
            embedding_model=os.getenv(
                "EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL
            ).strip()
            or DEFAULT_EMBEDDING_MODEL,
            local_embedding_model=os.getenv(
                "LOCAL_EMBEDDING_MODEL", DEFAULT_LOCAL_EMBEDDING_MODEL
            ).strip()
            or DEFAULT_LOCAL_EMBEDDING_MODEL,
            question_memory_max_items=_env_int("QUESTION_MEMORY_MAX_ITEMS", 500),
            question_memory_duplicate_distance=_env_float(
                "QUESTION_MEMORY_DUPLICATE_DISTANCE", 0.15
            ),
            enable_image_generation=_env_bool("ENABLE_IMAGE_GENERATION", False),
            image_model=os.getenv("IMAGE_MODEL", DEFAULT_IMAGE_MODEL).strip()
            or DEFAULT_IMAGE_MODEL,
            enable_llm_judge=_env_bool("ENABLE_LLM_JUDGE", False),
            chain_runtime=chain_runtime,  # type: ignore[arg-type]
            domain_profile=os.getenv("DOMAIN_PROFILE", DEFAULT_DOMAIN).strip()
            or DEFAULT_DOMAIN,
            response_style=os.getenv(
                "RESPONSE_STYLE", DEFAULT_RESPONSE_STYLE
            ).strip()
            or DEFAULT_RESPONSE_STYLE,
        )

    def validate(self) -> None:
        if self.provider == "openrouter":
            if not self.openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY is required for OpenRouter mode")
            if self.model not in COURSE_MODELS:
                raise ValueError(
                    f"OpenRouter model must be one of {', '.join(COURSE_MODELS)}"
                )
            if not self.openrouter_app_url.startswith(("http://", "https://")):
                raise ValueError("OPENROUTER_APP_URL must be an HTTP(S) URL")
            if self.openrouter_timeout_seconds <= 0:
                raise ValueError("openrouter_timeout_seconds must be positive")
        if self.provider == "local":
            if not self.local_base_url:
                raise ValueError("LOCAL_BASE_URL is required for local mode")
            if self.local_timeout_seconds <= 0:
                raise ValueError("local_timeout_seconds must be positive")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0 and 2")
        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError("top_p must be between 0 and 1")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")
        if self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive")
        if self.max_input_chars <= 0:
            raise ValueError("max_input_chars must be positive")
        if self.max_calls <= 0:
            raise ValueError("max_calls must be positive")
        if self.session_cost_cap_usd < 0:
            raise ValueError("session_cost_cap_usd must be zero or positive")
        if self.global_max_calls_per_day < 0:
            raise ValueError("global_max_calls_per_day must be zero or positive")
        if self.global_max_cost_per_day < 0:
            raise ValueError("global_max_cost_per_day must be zero or positive")
        if self.global_rate_per_minute < 0:
            raise ValueError("global_rate_per_minute must be zero or positive")
        if not 0.0 <= self.question_memory_duplicate_distance <= 2.0:
            raise ValueError(
                "question_memory_duplicate_distance must be between 0 and 2"
            )
        if self.chain_runtime not in ALLOWED_CHAIN_RUNTIMES:
            raise ValueError(f"chain_runtime must be one of {ALLOWED_CHAIN_RUNTIMES}")
        if self.response_style not in ALLOWED_RESPONSE_STYLES:
            raise ValueError(
                f"response_style must be one of {ALLOWED_RESPONSE_STYLES}"
            )

    def redacted(self) -> dict[str, object]:
        data = asdict(self)
        data["openrouter_api_key"] = "***" if self.openrouter_api_key else ""
        data["local_api_key"] = "***" if self.local_api_key else ""
        return data

    @property
    def has_openrouter_key(self) -> bool:
        return bool(self.openrouter_api_key)


SECRET_KEYS = frozenset(
    {
        "OPENROUTER_API_KEY",
        "OPENROUTER_MODEL",
        "OPENROUTER_APP_URL",
        "OPENROUTER_TIMEOUT_SECONDS",
        "LOCAL_API_KEY",
        "LOCAL_BASE_URL",
        "LOCAL_MODEL",
        "LOCAL_UNCAPPED_OUTPUT",
        "LOCAL_TIMEOUT_SECONDS",
        "TEMPERATURE",
        "MAX_OUTPUT_TOKENS",
        "MAX_CALLS",
        "MAX_INPUT_CHARS",
        "SESSION_COST_CAP_USD",
        "GLOBAL_MAX_CALLS_PER_DAY",
        "GLOBAL_MAX_COST_PER_DAY",
        "GLOBAL_RATE_PER_MINUTE",
        "STRICT_SAFETY",
        "ENABLE_LEXICAL_RAG",
        "ENABLE_QUESTION_MEMORY",
        "ENABLE_IMAGE_GENERATION",
        "ENABLE_LLM_JUDGE",
        "CHAIN_RUNTIME",
        "EMBEDDING_MODEL",
        "LOCAL_EMBEDDING_MODEL",
        "QUESTION_MEMORY_PATH",
        "QUESTION_MEMORY_MAX_ITEMS",
        "QUESTION_MEMORY_DUPLICATE_DISTANCE",
        "IMAGE_MODEL",
        "DOMAIN_PROFILE",
        "RESPONSE_STYLE",
        "TOP_P",
        "REASONING_EFFORT",
    }
)


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

    def text(key: str) -> str | None:
        value = values.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return None

    key = text("OPENROUTER_API_KEY")
    if key:
        updates["openrouter_api_key"] = key
        if settings.provider == "demo":
            updates["provider"] = "openrouter"
    for source, target in (
        ("OPENROUTER_MODEL", "model"),
        ("OPENROUTER_APP_URL", "openrouter_app_url"),
        ("LOCAL_API_KEY", "local_api_key"),
        ("LOCAL_BASE_URL", "local_base_url"),
        ("LOCAL_MODEL", "local_model"),
        ("EMBEDDING_MODEL", "embedding_model"),
        ("LOCAL_EMBEDDING_MODEL", "local_embedding_model"),
        ("QUESTION_MEMORY_PATH", "question_memory_path"),
        ("IMAGE_MODEL", "image_model"),
        ("DOMAIN_PROFILE", "domain_profile"),
    ):
        value = text(source)
        if value:
            updates[target] = value

    for source, target, default in (
        ("TEMPERATURE", "temperature", settings.temperature),
        ("TOP_P", "top_p", settings.top_p),
        ("MAX_CALLS", "max_calls", settings.max_calls),
        ("MAX_INPUT_CHARS", "max_input_chars", settings.max_input_chars),
        ("SESSION_COST_CAP_USD", "session_cost_cap_usd", settings.session_cost_cap_usd),
        (
            "GLOBAL_MAX_CALLS_PER_DAY",
            "global_max_calls_per_day",
            settings.global_max_calls_per_day,
        ),
        (
            "GLOBAL_MAX_COST_PER_DAY",
            "global_max_cost_per_day",
            settings.global_max_cost_per_day,
        ),
        (
            "GLOBAL_RATE_PER_MINUTE",
            "global_rate_per_minute",
            settings.global_rate_per_minute,
        ),
        (
            "QUESTION_MEMORY_MAX_ITEMS",
            "question_memory_max_items",
            settings.question_memory_max_items,
        ),
        (
            "QUESTION_MEMORY_DUPLICATE_DISTANCE",
            "question_memory_duplicate_distance",
            settings.question_memory_duplicate_distance,
        ),
        (
            "OPENROUTER_TIMEOUT_SECONDS",
            "openrouter_timeout_seconds",
            settings.openrouter_timeout_seconds,
        ),
        (
            "LOCAL_TIMEOUT_SECONDS",
            "local_timeout_seconds",
            settings.local_timeout_seconds,
        ),
    ):
        if source in values:
            if target in {
                "temperature",
                "top_p",
                "session_cost_cap_usd",
                "global_max_cost_per_day",
                "question_memory_duplicate_distance",
                "openrouter_timeout_seconds",
                "local_timeout_seconds",
            }:
                updates[target] = _coerce_float(values[source], default)
            else:
                updates[target] = _coerce_int(values[source], default)

    if "MAX_OUTPUT_TOKENS" in values:
        max_output = _coerce_int(
            values["MAX_OUTPUT_TOKENS"], settings.max_output_tokens
        )
        updates["max_output_tokens"] = max_output
        updates["max_tokens"] = max_output

    for source, target in (
        ("LOCAL_UNCAPPED_OUTPUT", "local_uncapped_output"),
        ("STRICT_SAFETY", "strict_safety"),
        ("ENABLE_LEXICAL_RAG", "enable_lexical_rag"),
        ("ENABLE_QUESTION_MEMORY", "enable_question_memory"),
        ("ENABLE_IMAGE_GENERATION", "enable_image_generation"),
        ("ENABLE_LLM_JUDGE", "enable_llm_judge"),
    ):
        if source in values:
            updates[target] = _coerce_bool(
                values[source], bool(getattr(settings, target))
            )

    chain = text("CHAIN_RUNTIME")
    if chain:
        updates["chain_runtime"] = _coerce_choice(
            chain, settings.chain_runtime, ALLOWED_CHAIN_RUNTIMES
        )
    style = text("RESPONSE_STYLE")
    if style:
        updates["response_style"] = _coerce_choice(
            style, settings.response_style, ALLOWED_RESPONSE_STYLES
        )
    reasoning = text("REASONING_EFFORT")
    if reasoning:
        updates["reasoning_effort"] = (
            reasoning if reasoning in ALLOWED_REASONING_EFFORTS else None
        )

    return replace(settings, **updates)
