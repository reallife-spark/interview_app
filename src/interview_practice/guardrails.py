"""Input and output rails for the interview practice app.

These are rule-based checks, not a security boundary. They make the common
failure modes visible and keep likely secrets out of model calls. The
defensive system prompt is the first layer; this module is the second.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class _SecretFinding:
    kind: str
    start: int
    end: int


_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("bearer_token", re.compile(r"(?i)\bbearer\s+[a-z0-9._-]{16,}")),
    ("openrouter_key", re.compile(r"\bsk-or-v1-[A-Za-z0-9_-]{16,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github_token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    (
        "credential_assignment",
        re.compile(
            r"(?i)\b(api[_-]?key|secret|password|token)\b\s*[:=]\s*"
            r"['\"]?[A-Za-z0-9_\-]{12,}"
        ),
    ),
)


class _SecretScanner:
    """Find and redact common credential shapes; not a complete detector."""

    def scan(self, text: str) -> list[_SecretFinding]:
        findings: list[_SecretFinding] = []
        for kind, pattern in _SECRET_PATTERNS:
            findings.extend(
                _SecretFinding(kind, match.start(), match.end())
                for match in pattern.finditer(text)
            )
        return sorted(findings, key=lambda finding: (finding.start, finding.end))

    def redact(self, text: str) -> str:
        redacted = text
        for kind, pattern in _SECRET_PATTERNS:
            redacted = pattern.sub(f"[REDACTED:{kind}]", redacted)
        return redacted


_INJECTION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "ignore_previous",
        re.compile(r"(?i)\bignore\s+(all\s+)?(previous|prior)\s+instructions?\b"),
    ),
    (
        "reveal_prompt",
        re.compile(
            r"(?i)\b(reveal|show|print|repeat)\b.{0,40}\b"
            r"(system\s+prompt|prompt|instructions)\b"
        ),
    ),
    (
        "prompt_extraction",
        re.compile(r"(?i)\b(repeat|print)\s+(the\s+)?(text|words)\s+above\b"),
    ),
    (
        "role_hijack",
        re.compile(
            r"(?i)\b(you\s+are\s+now|from\s+now\s+on\s+you\s+are)\b"
            r".{0,40}\b(general|unrestricted|different|assistant)\b"
        ),
    ),
    (
        "system_override",
        re.compile(r"(?i)\b(system|developer)\s+(prompt|message|instructions?)\b"),
    ),
    (
        "exfiltration",
        re.compile(r"(?i)\b(exfiltrate|upload|send)\b.{0,80}\bhttps?://"),
    ),
    (
        "canary_probe",
        re.compile(r"(?i)\b(canary|hidden\s+token)\b"),
    ),
)


class _InjectionDetector:
    """Rule-based prompt-injection detector; a layer, not a guarantee."""

    def detect(self, text: str) -> str | None:
        for name, pattern in _INJECTION_PATTERNS:
            if pattern.search(text):
                return name
        return None

    def detect_all(self, text: str) -> tuple[str, ...]:
        return tuple(
            name for name, pattern in _INJECTION_PATTERNS if pattern.search(text)
        )


@dataclass(frozen=True, slots=True)
class GuardrailResult:
    allowed: bool
    text: str
    warnings: tuple[str, ...] = ()
    blocked_reason: str | None = None
    matched_rules: tuple[str, ...] = ()
    canary_leaked: bool = False

    @property
    def state(self) -> str:
        if not self.allowed:
            return "blocked"
        if self.warnings:
            return "warned"
        return "allowed"


class GuardrailPipeline:
    """Check input and output text with a soft-flag default and strict option."""

    def __init__(
        self,
        *,
        max_input_chars: int = 8000,
        max_output_chars: int = 12_000,
        strict: bool = False,
    ) -> None:
        if max_input_chars <= 0 or max_output_chars <= 0:
            raise ValueError("character limits must be positive")
        self.max_input_chars = max_input_chars
        self.max_output_chars = max_output_chars
        self.strict = strict
        self._scanner = _SecretScanner()
        self._detector = _InjectionDetector()

    def check_input(self, text: str) -> GuardrailResult:
        if not text.strip():
            return GuardrailResult(False, "", blocked_reason="empty input")
        if len(text) > self.max_input_chars:
            return GuardrailResult(
                False,
                "",
                blocked_reason="input too large",
            )
        if self._scanner.scan(text):
            redacted = self._scanner.redact(text)
            return GuardrailResult(
                False,
                redacted,
                warnings=("secret detected and redacted",),
                blocked_reason="secret detected in input",
                matched_rules=("secret",),
            )
        rules = self._detector.detect_all(text)
        if rules:
            if self.strict:
                return GuardrailResult(
                    False,
                    text,
                    warnings=("injection pattern detected",),
                    blocked_reason=f"injection pattern: {rules[0]}",
                    matched_rules=rules,
                )
            return GuardrailResult(
                True,
                text,
                warnings=(f"possible injection pattern: {rules[0]}",),
                matched_rules=rules,
            )
        return GuardrailResult(True, text)

    def check_output(self, text: str, *, canary: str = "") -> GuardrailResult:
        if not text.strip():
            return GuardrailResult(False, "", blocked_reason="empty output")
        if len(text) > self.max_output_chars:
            return GuardrailResult(
                False,
                "",
                blocked_reason="output too large",
            )
        if self._scanner.scan(text):
            redacted = self._scanner.redact(text)
            return GuardrailResult(
                False,
                redacted,
                warnings=("secret detected and redacted",),
                blocked_reason="secret detected in output",
                matched_rules=("secret",),
            )
        warnings: list[str] = []
        rules: list[str] = []
        canary_leaked = bool(canary and canary in text)
        safe_text = text
        if canary_leaked:
            safe_text = text.replace(canary, "[REDACTED:CANARY]")
            warnings.append("canary leaked in output")
            rules.append("canary_leak")
        detected = self._detector.detect_all(text)
        if detected:
            warnings.append(f"possible injection pattern in output: {detected[0]}")
            rules.extend(detected)
        if self.strict and (canary_leaked or detected):
            return GuardrailResult(
                False,
                safe_text,
                warnings=tuple(warnings),
                blocked_reason=warnings[0] if warnings else "unsafe output",
                matched_rules=tuple(rules),
                canary_leaked=canary_leaked,
            )
        return GuardrailResult(
            True,
            safe_text,
            warnings=tuple(warnings),
            matched_rules=tuple(rules),
            canary_leaked=canary_leaked,
        )
