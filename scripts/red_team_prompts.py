#!/usr/bin/env python3
"""Run the offline red-team fixtures against the guardrail pipeline.

This script never calls a model. It is the reproducible evidence for the
off-topic and prompt-injection demo.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from interview_practice.guardrails import GuardrailPipeline  # noqa: E402


def run(fixture_path: Path) -> tuple[list[dict[str, str]], bool]:
    cases = json.loads(fixture_path.read_text(encoding="utf-8"))
    soft = GuardrailPipeline(max_input_chars=8000, strict=False)
    strict = GuardrailPipeline(max_input_chars=8000, strict=True)
    rows: list[dict[str, str]] = []
    passed = True
    for case in cases:
        text = str(case["text"])
        soft_state = soft.check_input(text).state
        strict_state = strict.check_input(text).state
        ok = (
            soft_state == case["soft_expected"]
            and strict_state == case["strict_expected"]
        )
        passed = passed and ok
        rows.append(
            {
                "id": str(case["id"]),
                "soft": soft_state,
                "strict": strict_state,
                "expected": f"{case['soft_expected']}/{case['strict_expected']}",
                "pass": "yes" if ok else "NO",
            }
        )
    return rows, passed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="offline fixture run")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "red_team.json",
    )
    args = parser.parse_args()

    rows, passed = run(args.fixture)
    if args.json:
        print(json.dumps({"passed": passed, "rows": rows}, indent=2))
    else:
        print("| Case | Soft | Strict | Expected | Pass |")
        print("|---|---|---|---|---|")
        for row in rows:
            print(
                f"| {row['id']} | {row['soft']} | {row['strict']} | "
                f"{row['expected']} | {row['pass']} |"
            )
        print()
        print("red-team fixtures: " + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
