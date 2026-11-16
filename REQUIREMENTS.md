---
title: Interview Practice App — requirements matrix
updated: 2026-11-16
sources:
  - 03_Sources/turing-college/interview-practice-app-brief-2026-11-16.md
  - 06_Projects/interview-practice-app/BRIEF.md
tags:
  - turing-college
  - sprint-1
  - requirements
---

# Interview Practice App — requirements matrix

Status values: `planned`, `in-progress`, `done`, `excluded`, `blocked`.
A requirement is `done` only after its check passes.

## Core requirements

| ID | Requirement | Implementation | Verification | Status |
|---|---|---|---|---|
| R1 | Single-page Streamlit app | `app.py` with three tabs | `AppTest` smoke test | done |
| R2 | OpenRouter API call | `providers/openrouter.py`; `/chat/completions` | mocked HTTP test | done |
| R3 | Course-allowed model | default `openai/gpt-6-luna`; chooser limited to the three listed models | config test | done |
| R4 | At least five system prompts with different techniques | six templates in `prompts/templates.py` | prompt tests + `PROMPTS.md` | done |
| R5 | Check which prompt works best | `scripts/evaluate_prompts.py` + `eval/summary.md` | demo run; live run when key present | done: offline fixture; live pending |
| R6 | Defensive system prompt | `prompts/guardrails.py`; stay-on-topic/ignore-override instructions | red-team fixtures | done |
| R7 | Off-topic and injection demo | `scripts/red_team_prompts.py`; `DEMO.md` | demo output captured | done |
| R8 | Real interview-preparation experience | Prepare, Practice, Coach flows | `AppTest` flow assertions | done |
| R9 | Job-description field | `tailoring.py`; `<job_description>` XML boundary | tailoring tests | done |
| R10 | Session-only chat history | `session.py`; no persistence | clear/export tests | done |
| R11 | Export and clear session | Markdown/JSON export; clear button | `AppTest` test | done |
| R12 | Demo mode | deterministic fixtures; default when no key | provider test | done |
| R13 | Local `agx64` developer mode | OpenAI-compatible provider at `http://127.0.0.1:21464/v1`; auto-detect `/v1/models` | mocked local test | done: mocked; tunnel not exercised |
| R14 | No silent provider fallback | provider selected explicitly; local failure stays local | provider test | done |
| R15 | Cost visibility | OpenRouter model metadata + token usage; per-call and session | cost tests | done |
| R16 | Model settings | model, temperature, `max_tokens`, `top_p`, `reasoning_effort` when supported | UI/config tests | done |
| R17 | Two structured JSON formats | `QuestionSet`, `AnswerEvaluation` schemas + parser | schema tests | done |
| R18 | Security guard | input validation, secret scan, injection detection, canary, strict toggle | guardrail tests | done |
| R19 | Developer settings separated from learner UX | sidebar “Developer settings” expander | `AppTest` test | done |
| R20 | README and run instructions | `README.md` | quickstart read-through | done |
| R21 | Prompt documentation | `PROMPTS.md` | technique coverage check | done |
| R22 | Security documentation | `SECURITY.md` | OWASP mapping and limitations | done |
| R23 | Evaluation documentation | `EVALUATION.md`; `eval/results.csv`; `eval/summary.md` | demo/live result recorded | done |
| R24 | Deployment documentation | `DEPLOYMENT.md`; Streamlit secrets | user-confirmed deploy | done |
| R25 | Course repo submission | `course` remote; push to `rmobil-AE.1.5` | user checks GitHub page | blocked: 403, authorize TuringCollegeSubmissions |
| R26 | Private backup repo | `interview_app` under `reallife-spark`; pushed, tag `v0.1.1` | user checks GitHub page | done |
| R27 | No secrets in tracked content | `.gitignore`; `.env.example`; secret scan | `git grep`/scanner | done |
| R28 | No live claim from development host | docs use “implemented and tested” or “not verified here” | doc review | done |
| R29 | Deadline discipline | MVP first; optional tasks after required features | timeline check | done |
| R30 | Review scheduling | user submits and books review | user confirmation | planned: waits on course repo |

## Bonus requirements

| ID | Requirement | Implementation | Verification | Status |
|---|---|---|---|---|
| B1 | All model settings | sliders/fields in sidebar | UI test | done |
| B2 | Two JSON formats | `QuestionSet`, `AnswerEvaluation` | schema tests | done |
| B3 | Prompt price | `cost.py` + OpenRouter models endpoint | cost test | done |
| B4 | OpenRouter docs improvement | model catalog drives picker, pricing, context length, supported parameters | config test | done |
| B5 | Job-description tailoring (RAG) | whole-text v1 + lexical RAG-lite | tailoring test | done |
| B6 | LLM chooser | three course models; local models in local mode | UI test | done |
| B7 | Security guard | soft/strict modes | guardrail test | done |
| B8 | Full chatbot | Coach tab with history | chat test | done |
| B9 | Prompt/model evaluation | deterministic rubric; optional live judge | eval test | done |

## Excluded requirements

| ID | Requirement | Reason |
|---|---|---|
| X1 | Image generation | Not selected; keeps the public app text-only and cheap |
| X2 | Excel jailbreak report | Replaced by a reproducible Markdown red-team table |
| X3 | LangChain | Sprint 2 topic; not needed for Sprint 1 |
| X4 | Vector database | Sprint 2 topic; lexical RAG-lite is the bounded substitute |
| X5 | Open-source-only model | Course defaults use OpenRouter; local mode is an extra |

## User-gated checks

| ID | Check | Gate | Status |
|---|---|---|---|
| G1 | GitHub account is `reallife-spark` and is the intended account | `gh auth status` and `gh api user` checked; email scope unavailable | done |
| G2 | Private repo `interview_app` may be created | explicit user request; created | done |
| G3 | Course repo push | `git ls-remote course` returned 403; wait for authorization | blocked |
| G4 | Streamlit Cloud deployment | user action; build agent prepares files | planned |
| G5 | Review booked | user action | planned |

## Evidence rules

- Offline tests prove code paths, not live model quality.
- A live OpenRouter run must record model, date, prompt variant and observed
  output; no aggregate claim beyond the sample.
- Local `agx64` checks prove that path only; the public app is OpenRouter.
- `03_Sources/` is read-only after capture.
