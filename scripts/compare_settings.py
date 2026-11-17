#!/usr/bin/env python3
"""Compare deterministic parameter combinations without pretending they are live.

Offline (default) runs the scripted demo provider. `--live` performs one
OpenRouter call per combination only when a key is present in the environment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from interview_practice.config import Settings  # noqa: E402
from interview_practice.engine import EngineError, InterviewEngine  # noqa: E402
from interview_practice.providers import build_provider  # noqa: E402

COMBINATIONS = (
    ("cool", 0.2, 1.0, 600),
    ("balanced", 0.7, 1.0, 900),
    ("hot", 1.0, 1.0, 900),
    ("narrow", 0.7, 0.8, 900),
    ("wide", 0.7, 1.0, 1200),
)


def _prompt_hash(engine: InterviewEngine) -> str:
    messages = engine.prompts.question_set(
        "json_schema",
        role="AI engineer",
        job_description="RAG and evaluation",
        difficulty="medium",
        count=1,
        canary=engine.session.canary,
        domain=engine.settings.domain_profile,
        style=engine.settings.response_style,
    )
    text = "\n".join(f"{message.role}:{message.content}" for message in messages)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def run_demo() -> list[dict[str, object]]:
    rows = []
    for name, temperature, top_p, max_tokens in COMBINATIONS:
        settings = Settings(
            provider="demo",
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        engine = InterviewEngine(
            settings,
            provider=build_provider(settings),
        )
        result = engine.generate_questions(
            role="AI engineer",
            job_description="RAG and evaluation",
            count=1,
        )
        rows.append(
            {
                "name": name,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "prompt_hash": _prompt_hash(engine),
                "model": result.usage.model,
                "provider": result.usage.provider,
                "latency_ms": result.usage.latency_ms,
                "cost_usd": result.usage.cost_usd,
                "question_id": result.question_set.questions[0].id,
            }
        )
    return rows


def run_live() -> list[dict[str, object]]:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise EngineError("OPENROUTER_API_KEY is required for --live")
    rows = []
    for name, temperature, top_p, max_tokens in COMBINATIONS:
        settings = Settings(
            provider="openrouter",
            openrouter_api_key=key,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        engine = InterviewEngine(settings)
        result = engine.generate_questions(
            role="AI engineer",
            job_description="RAG and evaluation",
            count=1,
        )
        rows.append(
            {
                "name": name,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "prompt_hash": _prompt_hash(engine),
                "model": result.usage.model,
                "provider": result.usage.provider,
                "latency_ms": result.usage.latency_ms,
                "cost_usd": result.usage.cost_usd,
                "question_id": result.question_set.questions[0].id,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="offline scripted run")
    parser.add_argument("--live", action="store_true", help="OpenRouter run")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()
    try:
        rows = run_live() if args.live else run_demo()
    except EngineError as exc:
        print(f"comparison unavailable: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for row in rows:
            print(
                f"{row['name']:9} temp={row['temperature']:<4} "
                f"top_p={row['top_p']:<4} max_tokens={row['max_tokens']:<5} "
                f"prompt={row['prompt_hash']} provider={row['provider']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
