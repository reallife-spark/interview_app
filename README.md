# Interview Practice Coach

A single-page Streamlit app for AI-engineering interview preparation. It
generates role-specific questions, evaluates written answers, and provides a
multi-turn coaching conversation. It is the Turing College Sprint 1 project
and uses OpenRouter.

**Public app:** <https://interviewap-nbsnftcgrwj7yjcm2h658m.streamlit.app/>.
It was smoke-tested in OpenRouter mode on 2026-11-17; see `DEPLOYMENT.md` for
the observed checks and cost. A fresh browser session loaded it on the same
date, and Cloud `agx64` discovery plus a `gemma4-2b-131k:latest` completion
passed. `curl` still gets a first-hop 303 as Streamlit bootstraps an anonymous
session; `scripts/smoke_public_app.sh` follows it and confirms the app title.
No key is in the repository.

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
- Structured interviewer rubrics with one schema-repair retry, an opt-in LLM judge, and an Excel red-team report.
- Optional Chroma question memory on an OpenAI-compatible embedding adapter, LangChain runtime and OpenRouter image generation.
- Budget-aware structured prompts and explicit output-cap errors instead of generic invalid-JSON failures.
- Reasoning effort gated by model metadata, with a visible one-time fallback when a model rejects it.
- A public `agx64` path through the authenticated `real-life.dev` VPS gateway.

## Modes

| Mode | Network | Key | Use |
|---|---|---|---|
| **Demo** | None | None | Default; deterministic fixtures; review demo |
| **OpenRouter** | Yes | `OPENROUTER_API_KEY` | Public app and live model calls |
| **agx64** | Public HTTPS gateway | Gateway token | Local/open-source model path |

The local path uses the authenticated gateway `https://real-life.dev/v1`
(`VPS.md`); the older SSH tunnel remains a developer option at
`http://127.0.0.1:21464/v1`. There is **no silent fallback** from `agx64` to
OpenRouter because a job description can be private.

## Course-allowed models

- `openai/gpt-6-luna` — default
- `anthropic/claude-sonnet-5.5`
- `openai/gpt-6.1-sol`

The OpenRouter side of the unified selector is limited to those three. The
`agx64` side lists the models returned by `/v1/models`.

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
                 -> retrieval (optional Chroma question memory)
                 -> reports / imagegen / judge (optional artifacts)
                 -> session (call/cost caps, history, canary)
                 -> schemas (QuestionSet, AnswerEvaluation, Rubric, Judge)
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
  retrieval/         optional Chroma question memory
  reports.py         Excel red-team workbook
  imagegen.py        opt-in OpenRouter image action
  providers/         build_provider; base contract; _lib adapters; tests
  prompts/           PromptLibrary; public schemas/techniques; _lib; tests
  ui/                render_app; _lib layout; tests
tests/               root-module unit tests
scripts/             check, evaluation, red-team and smoke CLIs
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
python scripts/compare_settings.py --demo
python scripts/jailbreak_report.py --demo
LOCAL_API_KEY=... ./scripts/smoke_gateway.sh
./scripts/smoke_public_app.sh
```

`scripts/check.sh` runs pytest, Ruff and `PYTHONPATH=src lint-imports`.

Evidence recorded on **2026-11-17** on this host:

- 114 tests pass.
- Ruff reports 0 findings.
- 8 import-linter contracts kept; the pass/fail/revert proof is documented in
  `src/interview_practice/README.md`.
- Headless Streamlit starts and returns HTTP 200.
- The offline evaluation runs 18 rows; `json_schema` ranks first at 9.62/10 in the fixture.
- A dated live sample (2026-11-17) had 18/18 valid rows; `cot` scored 9.45/10 in that sample; it is a small sample, not a general claim.
- Vault `./scripts/validate.sh` passes.

The public Streamlit URL loads in a fresh headless browser, and the 2026-11-17
OpenRouter smoke was observed from this build host. The `agx64` gateway was
checked directly and through the Cloud app on 2026-11-17; Cloud discovery and a
`gemma4-2b-131k:latest` completion passed. No general live-service or
model-quality claim is made.

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
- [`REVIEW_EXPLANATIONS.md`](../../REVIEW_EXPLANATIONS.md) — cited concept → app explanations for every substantive course-brief item (at vault root).
- `DEMO.md` — a five-minute review script.
- `DEPLOYMENT.md` — local setup, Streamlit Cloud runbook, GitHub remotes and submission.
- `.streamlit/secrets.toml.example` — secret names for Streamlit Cloud, no values.
- `HANDOFF.md` — current repo state and the course-access blocker.
- `COURSE_COMPLIANCE.md` — Sprint 1 requirement and link coverage.
- `BRIEF.md` and `REQUIREMENTS.md` — course mapping and status.

## Limitations

- The offline evaluation is a fixture, not a live model-quality result.
- Chroma question memory is optional and uses provider-scoped collections.
- LangChain is an optional runtime; native remains the default.
- Image generation and the LLM judge are opt-in and mocked in tests; no live
  image or judge quality claim is made.
- The guardrails are rule-based and can miss paraphrased attacks.
- A public app needs its own OpenRouter key and spend cap; a shared key is not
  provided here.
- No screenshot was captured in this terminal-only environment; `DEMO.md`
  provides a textual walkthrough.

## License

MIT. See `LICENSE`.
