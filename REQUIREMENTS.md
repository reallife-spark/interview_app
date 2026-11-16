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
| R1 | Single-page Streamlit app | `app.py` with three tabs | `AppTest` smoke test | planned |
| R2 | OpenRouter API call | `providers/openrouter.py`; `/chat/completions` | mocked HTTP test | planned |
| R3 | Course-allowed model | default `openai/gpt-6-luna`; chooser limited to the three listed models | config test | planned |
| R4 | At least five system prompts with different techniques | six templates in `prompts/templates.py` | prompt tests + `PROMPTS.md` | planned |
| R5 | Check which prompt works best | `scripts/evaluate_prompts.py` + `eval/summary.md` | demo run; live run when key present | planned |
| R6 | Defensive system prompt | `prompts/guardrails.py`; stay-on-topic/ignore-override instructions | red-team fixtures | planned |
| R7 | Off-topic and injection demo | `scripts/red_team_prompts.py`; `DEMO.md` | demo output captured | planned |
| R8 | Real interview-preparation experience | Prepare, Practice, Coach flows | `AppTest` flow assertions | planned |
| R9 | Job-description field | `tailoring.py`; `<job_description>` XML boundary | tailoring tests | planned |
| R10 | Session-only chat history | `session.py`; no persistence | clear/export tests | planned |
| R11 | Export and clear session | Markdown/JSON export; clear button | `AppTest` test | planned |
| R12 | Demo mode | deterministic fixtures; default when no key | provider test | planned |
| R13 | Local `agx64` developer mode | OpenAI-compatible provider at `http://127.0.0.1:21464/v1`; auto-detect `/v1/models` | mocked local test | planned |
| R14 | No silent provider fallback | provider selected explicitly; local failure stays local | provider test | planned |
| R15 | Cost visibility | OpenRouter model metadata + token usage; per-call and session | cost tests | planned |
| R16 | Model settings | model, temperature, `max_tokens`, `top_p`, `reasoning_effort` when supported | UI/config tests | planned |
| R17 | Two structured JSON formats | `QuestionSet`, `AnswerEvaluation` schemas + parser | schema tests | planned |
| R18 | Security guard | input validation, secret scan, injection detection, canary, strict toggle | guardrail tests | planned |
| R19 | Developer settings separated from learner UX | sidebar “Developer settings” expander | `AppTest` test | planned |
| R20 | README and run instructions | `README.md` | quickstart read-through | planned |
| R21 | Prompt documentation | `PROMPTS.md` | technique coverage check | planned |
| R22 | Security documentation | `SECURITY.md` | OWASP mapping and limitations | planned |
| R23 | Evaluation documentation | `EVALUATION.md`; `eval/results.csv`; `eval/summary.md` | demo/live result recorded | planned |
| R24 | Deployment documentation | `DEPLOYMENT.md`; Streamlit secrets | user-confirmed deploy | planned |
| R25 | Course repo submission | `course` remote; push to `rmobil-AE.1.5` | user checks GitHub page | planned |
| R26 | Private backup repo | `interview_app` under `reallife-spark` | user checks GitHub page | planned |
| R27 | No secrets in tracked content | `.gitignore`; `.env.example`; secret scan | `git grep`/scanner | planned |
| R28 | No live claim from development host | docs use “implemented and tested” or “not verified here” | doc review | planned |
| R29 | Deadline discipline | MVP first; optional tasks after required features | timeline check | planned |
| R30 | Review scheduling | user submits and books review | user confirmation | planned |

## Bonus requirements

| ID | Requirement | Implementation | Verification | Status |
|---|---|---|---|---|
| B1 | All model settings | sliders/fields in sidebar | UI test | planned |
| B2 | Two JSON formats | `QuestionSet`, `AnswerEvaluation` | schema tests | planned |
| B3 | Prompt price | `cost.py` + OpenRouter models endpoint | cost test | planned |
| B4 | OpenRouter docs improvement | model catalog drives picker, pricing, context length, supported parameters | config test | planned |
| B5 | Job-description tailoring (RAG) | whole-text v1 + lexical RAG-lite | tailoring test | planned |
| B6 | LLM chooser | three course models; local models in local mode | UI test | planned |
| B7 | Security guard | soft/strict modes | guardrail test | planned |
| B8 | Full chatbot | Coach tab with history | chat test | planned |
| B9 | Prompt/model evaluation | deterministic rubric; optional live judge | eval test | planned |

## Excluded requirements

| ID | Requirement | Reason |
|---|---|---|
| X1 | Image generation | Not selected; keeps the public app text-only and cheap |
| X2 | Excel jailbreak report | Replaced by a reproducible Markdown red-team table |
| X3 | LangChain | Sprint 2 topic; not needed for Sprint 1 |
| X4 | Vector database | Sprint 2 topic; lexical RAG-lite is the bounded substitute |
| X5 | Open-source-only model | Course defaults use OpenRouter; local mode is an extra |

## User-gated checks

| ID | Check | Gate |
|---|---|---|
| G1 | GitHub account is `reallife-spark` and belongs to SparkNet | `gh auth status` read-only check; email scope unavailable |
| G2 | Private repo `interview_app` may be created | explicit confirmation before `gh repo create` |
| G3 | Course repo push | explicit confirmation before `git push course main` |
| G4 | Streamlit Cloud deployment | user action; build agent prepares files |
| G5 | Review booked | user action |

## Evidence rules

- Offline tests prove code paths, not live model quality.
- A live OpenRouter run must record model, date, prompt variant and observed
  output; no aggregate claim beyond the sample.
- Local `agx64` checks prove that path only; the public app is OpenRouter.
- `03_Sources/` is read-only after capture.
