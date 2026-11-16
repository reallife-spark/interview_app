"""Streamlit entry point for the Interview Practice App.

Run locally with:

    streamlit run app.py

The full UI is assembled in Step 67. This entry point keeps the import and
page configuration stable while the package is built out.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from interview_practice import __version__  # noqa: E402

st.set_page_config(
    page_title="Interview Practice Coach",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Interview Practice Coach")
st.caption(f"v{__version__} — Turing College Sprint 1")
st.info(
    "Scaffold ready. The provider, prompt, safety, and practice surfaces are "
    "implemented in Phase 10 Steps 63–67."
)
