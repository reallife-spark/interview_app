#!/usr/bin/env python3
"""Build the defensive red-team workbook."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from interview_practice.reports import (  # noqa: E402
    load_fixtures,
    write_jailbreak_report,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=ROOT / "tests" / "fixtures" / "red_team.json",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "reports" / "jailbreak-report.xlsx",
    )
    parser.add_argument("--demo", action="store_true", help="use fixture rows only")
    args = parser.parse_args()
    fixtures = load_fixtures(args.fixtures)
    path = write_jailbreak_report(args.out, fixtures)
    print(f"fixtures: {len(fixtures)}")
    print(f"workbook: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
