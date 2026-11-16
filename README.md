# Interview Practice Coach

A single-page Streamlit app for AI-engineering interview preparation. It
generates role-specific questions, evaluates written answers, and provides a
multi-turn coaching conversation. It is the Turing College Sprint 1 project
and uses OpenRouter.

## What it demonstrates

- A real Streamlit UI with **Prepare**, **Practice** and **Coach** surfaces.
- Six system-prompt techniques, selectable in the developer settings.
- Two structured JSON outputs: `QuestionSet` and `AnswerEvaluation`.
- A defensive system prompt plus input/output guardrails for off-topic and
  prompt-injection attempts.
- Job-description tailoring with a bounded lexical RAG-lite path.
- Model settings, model chooser, price estimate and session caps.
- A multi-turn chatbot, not only one-time calls.
- A deterministic prompt-comparison harness with an offline fixture run.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# Add OPENROUTER_API_KEY to .env, or leave it empty for demo mode.
streamlit run app.py
```

Open `http://localhost:8501`.

> If this project lives inside the AIengin vault, keep `.venv` outside the
> vault or remove it before `./scripts/validate.sh`: the vault's secret-file
> scan treats bundled certificate `.pem` files as secret-shaped.

## Modes

| Mode | Network | Key | Use |
|---|---|---|---|
| **Demo** | None | None | Default; deterministic fixtures; review demo |
| **OpenRouter** | Yes | `OPENROUTER_API_KEY` | Public app and live model calls |
| **Local** | Local tunnel | Optional | Developer checks against `agx64` |

Local mode uses an OpenAI-compatible endpoint at
`http://127.0.0.1:21464/v1` (the existing SSH tunnel). The public app is
OpenRouter; there is **no silent fallback** from local to OpenRouter because a
job description can be private.

## Course-allowed models

- `openai/gpt-6-luna` — default
- `anthropic/claude-sonnet-5.5`
- `openai/gpt-6.1-sol`

The public model chooser is limited to those three. Local mode lists only the
models returned by `/v1/models`.

## Architecture

```text
app.py
  -> interview_practice.ui.layout
       -> interview_practice.engine
            -> providers (OpenRouter / local / demo)
            -> prompts (six techniques + defensive prompt)
            -> guardrails (secrets, injection, canary)
            -> tailoring (job-description cap + BM25-lite)
            -> session (call/cost caps, history, canary)
            -> schemas (QuestionSet, AnswerEvaluation)
```

The engine is independent of Streamlit and is covered by unit tests. The UI is
covered by `streamlit.testing.v1.AppTest` in demo mode.

## Project layout

```text
app.py
src/interview_practice/
  config.py          environment and course models
  engine.py          provider + prompt + safety + budget service
  cost.py            model catalog and cost estimates
  guardrails.py      secret/injection/canary checks
  tailoring.py       job-description cap and lexical retrieval
  session.py         session caps and exported history
  evaluation.py      prompt comparison rubric and runners
  providers/         OpenRouter, local, demo
  prompts/           defensive prompt, templates, schemas
  ui/                Streamlit layout
tests/               unit and AppTest coverage
scripts/             evaluation and red-team CLIs
eval/                demo results and summary
```

## Checks

```bash
pytest -q
ruff check .
python scripts/evaluate_prompts.py --demo
python scripts/red_team_prompts.py --demo
```

Evidence recorded on **2026-11-16** on this host:

- 69 tests pass.
- Ruff reports 0 findings.
- Headless Streamlit starts and returns HTTP 200.
- The offline evaluation runs 18 rows; `json_schema` ranks first in the fixture.
- Vault `./scripts/validate.sh` passes.

This is **implemented and tested**, not a live deployment claim.

## Safety and privacy

- No secret is written to a page, log, commit or command output.
- Job descriptions and answers are treated as untrusted data.
- The app refuses off-topic requests and attempts to override its instructions.
- A per-session canary detects prompt leakage.
- Secret-shaped input is blocked and redacted.
- Session history is in memory only; export is explicit.
- `SECURITY.md` states the limits: rule-based detection is a layer, not a
  guarantee.

## Documentation

- `PROMPTS.md` — six techniques, defensive layer and JSON shapes.
- `SECURITY.md` — threat model, controls, OWASP mapping and limits.
- `EVALUATION.md` — prompt comparison method and offline result.
- `DEMO.md` — a five-minute review script.
- `DEPLOYMENT.md` — local setup, Streamlit Cloud, GitHub remotes and submission.
- `BRIEF.md` and `REQUIREMENTS.md` — course mapping and status.

## Limitations

- The offline evaluation is a fixture, not a live model-quality result.
- The lexical RAG-lite path is not a vector database; Sprint 2 covers that.
- The guardrails are rule-based and can miss paraphrased attacks.
- A public app needs its own OpenRouter key and spend cap; a shared key is not
  provided here.
- No screenshot was captured in this terminal-only environment; `DEMO.md`
  provides a textual walkthrough.

## License

MIT. See `LICENSE`.
