"""Excel workbooks for the defensive red-team report."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

FORMULA_PREFIXES = ("=", "+", "-", "@")


@dataclass(frozen=True, slots=True)
class ReportPaths:
    fixtures: Path


def load_fixtures(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("fixture file must contain a JSON array")
    return [dict(item) for item in payload if isinstance(item, Mapping)]


def safe_cell(value: object) -> object:
    """Prevent a text value from becoming an Excel formula."""

    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def _write_table(ws, headers: Iterable[str], rows: Iterable[Iterable[object]]) -> None:
    header_row = list(headers)
    ws.append([safe_cell(value) for value in header_row])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
    for row in rows:
        ws.append([safe_cell(value) for value in row])
    for index, header in enumerate(header_row, start=1):
        width = max(12, min(60, len(header) + 4))
        ws.column_dimensions[get_column_letter(index)].width = width
    ws.freeze_panes = "A2"


def build_jailbreak_workbook(
    fixtures: Iterable[Mapping[str, Any]],
    *,
    live_rows: Iterable[Mapping[str, Any]] = (),
    generated_at: datetime | None = None,
) -> bytes:
    """Return a deterministic workbook with summary, fixtures and controls."""

    fixture_rows = [dict(row) for row in fixtures]
    live = [dict(row) for row in live_rows]
    stamp = (generated_at or datetime.now(UTC)).isoformat(timespec="seconds")
    workbook = Workbook()

    summary = workbook.active
    summary.title = "Summary"
    summary["A1"] = "Interview Practice App — red-team report"
    summary["A1"].font = Font(bold=True, size=14)
    summary["A3"] = "Generated (UTC)"
    summary["B3"] = stamp
    summary["A4"] = "Fixture rows"
    summary["B4"] = len(fixture_rows)
    summary["A5"] = "Live rows"
    summary["B5"] = len(live)
    summary["A6"] = "Scope"
    summary["B6"] = (
        "Rule-based guardrail fixtures. Not a live model or security audit."
    )
    summary["A7"] = "Formula safety"
    summary["B7"] = "Text beginning with =, +, - or @ is prefixed with an apostrophe."
    summary.column_dimensions["A"].width = 22
    summary.column_dimensions["B"].width = 80

    fixtures_ws = workbook.create_sheet("Fixtures")
    _write_table(
        fixtures_ws,
        ("ID", "Prompt", "Soft expected", "Strict expected"),
        (
            (
                row.get("id", ""),
                row.get("text", ""),
                row.get("soft_expected", ""),
                row.get("strict_expected", ""),
            )
            for row in fixture_rows
        ),
    )

    live_ws = workbook.create_sheet("Live")
    _write_table(
        live_ws,
        ("ID", "Provider", "Model", "Observed", "Note"),
        (
            (
                row.get("id", ""),
                row.get("provider", ""),
                row.get("model", ""),
                row.get("observed", ""),
                row.get("note", ""),
            )
            for row in live
        ),
    )

    controls = workbook.create_sheet("Controls")
    _write_table(
        controls,
        ("Control", "Status", "Evidence"),
        (
            ("Defensive system prompt", "implemented", "prompts integrity tests"),
            ("Rule-based input/output rails", "implemented", "guardrail tests"),
            ("Session call/cost caps", "implemented", "session tests"),
            ("Process-wide daily/rate/cost guard", "implemented", "session tests"),
            ("OpenRouter spend limit", "owner action", "OpenRouter dashboard"),
            ("Public gateway bearer token", "implemented", "nginx 401/200 check"),
            ("WireGuard link", "implemented", "wg handshake and ping"),
            ("Live model audit", "not run", "outside the fixture run"),
        ),
    )

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def write_jailbreak_report(
    path: Path,
    fixtures: Iterable[Mapping[str, Any]],
    *,
    live_rows: Iterable[Mapping[str, Any]] = (),
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(build_jailbreak_workbook(fixtures, live_rows=live_rows))
    return path
