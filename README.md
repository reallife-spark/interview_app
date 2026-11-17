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
- Job-description tailoring with a bounded hybrid RAG-lite path (BM25 + hashed vectors + RRF).
- Model settings, model chooser, live catalog pricing, last-call usage and session caps.
- A multi-turn chatbot with strict, neutral and friendly interviewer styles.
- A deterministic prompt-comparison harness with an offline fixture run.

## Quick start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
# Add OPENROUTER_API_KEY to .env, or leave it empty for demo mode.
# The app loads .env automatically; never commit it.
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
  -> interview_practice.ui (render_app)
       -> ui._lib.layout
            -> interview_practice.engine
                 -> providers (build_provider + private adapters)
                 -> prompts (PromptLibrary + private templates)
                 -> guardrails (secrets, injection, canary)
                 -> tailoring (job-description cap + hybrid RAG-lite)
                 -> session (call/cost caps, history, canary)
                 -> schemas (QuestionSet, AnswerEvaluation)
```

The engine is independent of Streamlit and is covered by unit tests. The UI is
covered by `streamlit.testing.v1.AppTest` in demo mode.

## Project layout

```text
app.py
src/interview_practice/
  messages.py        neutral ChatMessage type
  config.py          environment and course models
  engine.py          provider + prompt + safety + budget service
  cost.py            model catalog and cost estimates
  guardrails.py      secret/injection/canary checks
  tailoring.py       job-description cap and hybrid RAG-lite
  session.py         session caps, usage history and exported history
  usage.py           CallUsage records for observability
  evaluation.py      prompt comparison rubric and runners
  providers/         build_provider; base contract; _lib adapters; tests
  prompts/           PromptLibrary; public schemas/techniques; _lib; tests
  ui/                render_app; _lib layout; tests
tests/               root-module unit tests
scripts/             check, evaluation and red-team CLIs
eval/                demo results and summary
```

## Module boundaries

- Root package: `interview_practice`. The project deliberately does **not** use
  `src/packages/`.
- `ui` exposes `render_app`; its layout is `ui/_lib/layout.py`.
- `providers` exposes `build_provider` and the provider contract; concrete
  adapters are `providers/_lib/`.
- `prompts` exposes `PromptLibrary` and technique options; templates, catalog
  and defensive prompt are `prompts/_lib/`; schemas stay public.
- Tests for those subpackages live under their `tests/` trees and import only
  the entry point. Root-module tests remain under top-level `tests/`.
- Import only a subpackage entry point or public root module; never `_lib`.
- See `src/interview_practice/README.md` for the gate and the proof it bites.

## Checks

```bash
./scripts/check.sh
python scripts/evaluate_prompts.py --demo
python scripts/red_team_prompts.py --demo
```

`scripts/check.sh` runs pytest, Ruff and `PYTHONPATH=src lint-imports`.

Evidence recorded on **2026-11-17** on this host:

- 79 tests pass.
- Ruff reports 0 findings.
- 8 import-linter contracts kept; the pass/fail/revert proof is documented in
  `src/interview_practice/README.md`.
- Headless Streamlit starts and returns HTTP 200.
- The offline evaluation runs 18 rows; `json_schema` ranks first at 9.62/10 in the fixture.
- A dated live sample (2026-11-17) had 18/18 valid rows; `cot` scored 9.45/10 in that sample; it is a small sample, not a general claim.
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

- `USER_MANUAL.md` — the full user guide: modes, screens, settings, safety,
  cost, export and troubleshooting.
- `RESEARCH.md` — the AI-engineering interview domain and design assumptions.
- `PROMPTS.md` — six techniques, defensive layer and JSON shapes.
- `SECURITY.md` — threat model, controls, OWASP mapping and limits.
- `EVALUATION.md` — prompt comparison method and offline result.
- `DEMO.md` — a five-minute review script.
- `DEPLOYMENT.md` — local setup, Streamlit Cloud, GitHub remotes and submission.
- `HANDOFF.md` — current repo state and the course-access blocker.
- `COURSE_COMPLIANCE.md` — Sprint 1 requirement and link coverage.
- `BRIEF.md` and `REQUIREMENTS.md` — course mapping and status.

## Limitations

- The offline evaluation is a fixture, not a live model-quality result.
- The hybrid RAG-lite path is not a vector database; Sprint 2 covers that.
- The guardrails are rule-based and can miss paraphrased attacks.
- A public app needs its own OpenRouter key and spend cap; a shared key is not
  provided here.
- No screenshot was captured in this terminal-only environment; `DEMO.md`
  provides a textual walkthrough.

## License

MIT. See `LICENSE`.
