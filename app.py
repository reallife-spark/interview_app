"""Streamlit entry point for the Interview Practice App.

Run locally with:

    streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from interview_practice.ui.layout import render_app  # noqa: E402

render_app()
