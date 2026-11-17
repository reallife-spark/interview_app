"""Response-style profiles for concise and detailed answers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResponseStyle:
    key: str
    label: str
    instruction: str


RESPONSE_STYLES: tuple[ResponseStyle, ...] = (
    ResponseStyle(
        key="balanced",
        label="Balanced",
        instruction="Be specific and complete without padding.",
    ),
    ResponseStyle(
        key="concise",
        label="Concise",
        instruction="Prefer short, high-signal answers and brief bullets.",
    ),
    ResponseStyle(
        key="detailed",
        label="Detailed",
        instruction=(
            "Explain reasoning, trade-offs and examples in more depth, while "
            "remaining focused."
        ),
    ),
)

_STYLE_BY_KEY = {style.key: style for style in RESPONSE_STYLES}
DEFAULT_STYLE = "balanced"


def get_style(key: str) -> ResponseStyle:
    return _STYLE_BY_KEY.get(key, _STYLE_BY_KEY[DEFAULT_STYLE])


def style_options() -> tuple[ResponseStyle, ...]:
    return RESPONSE_STYLES
