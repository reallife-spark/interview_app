# Interview Practice Coach

A single-page Streamlit app for AI-engineering interview preparation. It
generates role-specific questions, evaluates written answers, and provides a
multi-turn coaching conversation. It is built for the Turing College Sprint 1
project and uses OpenRouter.

> The full documentation is written in Step 70. This page currently records the
> scaffold and the local run contract.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# Add OPENROUTER_API_KEY to .env, or leave it empty for demo mode.
streamlit run app.py
```

## Modes

- **Demo** — deterministic fixtures; no network or key required.
- **OpenRouter** — the public app path; requires `OPENROUTER_API_KEY`.
- **Local** — developer-only path through the `agx64` OpenAI-compatible tunnel
  at `http://127.0.0.1:21464/v1`.

There is no silent fallback between providers.

## Checks

```bash
pytest -q
ruff check .
./scripts/validate.sh   # from the vault root
```

## Project status

Phase 10, Step 62: scaffold. See `../../PLAN.md` and
`../../06_Projects/interview-practice-app/BRIEF.md` for the work order.
