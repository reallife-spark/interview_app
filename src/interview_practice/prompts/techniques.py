"""Public prompt-technique records."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Technique:
    key: str
    label: str
    description: str
