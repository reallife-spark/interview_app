#!/usr/bin/env python3
"""Run the prompt comparison harness.

Offline (default):

    python scripts/evaluate_prompts.py --demo

Live OpenRouter:

    OPENROUTER_API_KEY=... python scripts/evaluate_prompts.py --live \
      --model openai/gpt-6-luna
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from interview_practice.config import DEFAULT_MODEL  # noqa: E402
from interview_practice.engine import EngineError  # noqa: E402
from interview_practice.evaluation import (  # noqa: E402
    run_demo,
    run_live,
    write_results,
    write_summary,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="offline fixture run")
    parser.add_argument("--live", action="store_true", help="OpenRouter run")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "eval")
    args = parser.parse_args()

    if args.live:
        try:
            rows = run_live(model=args.model)
        except EngineError as exc:
            print(f"live evaluation unavailable: {exc}", file=sys.stderr)
            return 2
        results_path = args.out_dir / "results.live.csv"
        summary_path = args.out_dir / "summary.live.md"
        mode = "live"
        summary_model = args.model
    else:
        rows = run_demo()
        results_path = args.out_dir / "results.csv"
        summary_path = args.out_dir / "summary.md"
        mode = "demo"
        summary_model = "scripted/interview-fixture (offline fixture)"

    write_results(rows, results_path)
    best = write_summary(
        rows,
        summary_path,
        mode=mode,
        model=summary_model,
    )
    print(f"rows: {len(rows)}")
    print(f"best technique: {best}")
    print(f"results: {results_path}")
    print(f"summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
