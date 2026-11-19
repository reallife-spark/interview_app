---
title: Turing College Sprint 1 — compliance map
updated: 2026-11-19
sources:
  - 03_Sources/turing-college/interview-practice-app-brief-2026-11-16.md
  - 03_Sources/turing-college/sprint-1-course-status-2026-11-16.md
  - https://intra.turingcollege.com/hardskills/build-an-interview-practice-app
tags:
  - turing-college
  - sprint-1
  - compliance
  - interview-practice
---

# Turing College Sprint 1 — compliance map

This page maps the LMS requirements to the app and records what is complete,
what is partial and what is blocked. It is not a claim that the course is
submitted.

## Course status

| Item | State |
|---|---|
| Part 1 — Development Environment and APIs | Done |
| Part 2 — Introduction to Prompt Engineering | Done |
| Part 3 — Prompt Evaluation & LLM Benchmarks | Done |
| Part 4 — Build an Interview Practice App | In progress |
| Project start | October 24 |
| LMS status on 2026-11-16 | 3 days left |
| Deadline | November 20 |
| Estimated effort | 5 hours |

The canonical page is
`https://intra.turingcollege.com/hardskills/build-an-interview-practice-app`.
The unauthenticated fetch returned HTTP 404 on 2026-11-16; the captured
user-pasted text is authoritative.

## Required task coverage

| Requirement | Evidence | Status |
|---|---|---|
| Research the interview-preparation domain | `RESEARCH.md`; `BRIEF.md` domain choice | Done |
| Single-page front-end using Streamlit | `app.py`; three tabs; `ui/_lib/layout.py` | Done |
| Call OpenRouter | `providers/_lib/openrouter.py`; `Provider.complete(CompletionRequest)` | Done; dated live sample 2026-11-17 |
| Use a course-allowed model | default `openai/gpt-6-luna`; three-model chooser | Done |
| At least 5 system prompts with different techniques | six techniques in `PromptLibrary`; `PROMPTS.md` | Done |
| Check which prompt works best | `scripts/evaluate_prompts.py`; `EVALUATION.md`; offline + dated live sample | Done |
| Defensive system prompt | `prompts/_lib/defensive.py`; `GuardrailPipeline`; `SECURITY.md` | Done |
| Off-topic demo | `DEMO.md`; defensive-prompt tests | Done: prompt-level + manual demo |
| Prompt-injection demo | red-team fixtures; `DEMO.md`; strict mode | Done |
| UI for a real interview-preparation experience | Prepare / Practice / Coach; `AppTest` | Done |
| Reflection and improvement | `README.md` limitations; `USER_MANUAL.md`; `RESEARCH.md` | Done |

## Bonus task coverage

| Task | Evidence | Status |
|---|---|---|
| All model settings | model, temperature, max tokens, top-p, reasoning effort in sidebar | Done |
| Two JSON formats | `QuestionSet`, `AnswerEvaluation`; parser and schema tests | Done |
| Prompt price | `cost.py`; OpenRouter model catalog; last-call usage | Done |
| OpenRouter docs improvement | catalog drives pricing, context, supported parameters and request gating | Done |
| Job description (RAG) | `tailoring.py`; whole-text and hybrid RAG-lite | Done |
| LLM chooser | three course models; local model discovery | Done |
| Security guard | `GuardrailPipeline`; soft/strict modes; canary | Done |
| Full chatbot | Coach tab with session history | Done |
| Interviewer personas | strict/neutral/friendly selector; `PromptLibrary.chat(..., persona=...)` | Done |
| Assessment via LLM-as-judge or other | deterministic rubric; dated live sample; no judge score claimed | Done |

## Optional task completion (Phase 16)

All easy, medium and hard optional tasks are implemented or explicitly
evidenced. The evidence is code plus tests; mocked tests are not live-model
quality claims.

| Task | Evidence | Status |
|---|---|---|
| E1 critique | `APP_CRITIQUE.md` | Done |
| E2 domain profiles | `prompts/domains.py`; domain tests | Done |
| E3 prompt integrity and input caps | `prompts/integrity.py`; `engine.py` field caps; tests | Done |
| E4 difficulty | Prepare selector; schema tests | Done |
| E5 response styles | `prompts/styles.py`; style tests | Done |
| E6 interviewer rubric | `InterviewRubric`; engine/UI; rubric tests | Done |
| E7 personas | Coach selector; persona tests | Done |
| E8 setting comparison | `scripts/compare_settings.py --demo` | Done |
| M1 all model settings | sidebar controls and config tests | Done |
| M2 JSON formats | questions, evaluation, rubric, judge schemas | Done |
| M3 prompt price | catalog pricing and usage/cost display | Done |
| M4 OpenRouter improvement | capability-aware catalog and unified selector | Done |
| M5 Excel jailbreak report | `reports.py`; CLI; workbook download/test | Done |
| M6 job-description RAG | `tailoring.py`; hybrid RAG-lite tests | Done |
| M7 LLM chooser | unified Model selector; OpenRouter + `agx64` | Done |
| M8 image generation | `imagegen.py` and mocked test retained; UI action removed 2026-11-19 | Partial: backend only; not live-tested |
| M9 security guard and developer separation | `guardrails.py`; Developer settings; tests | Done |
| H1 full chatbot | Coach tab with history | Done |
| H2 LangChain | optional `LangChainProvider`; native default | Done: mocked/native default |
| H3 vector database | Chroma question memory; provider-scoped; duplicate test | Done: Chroma test |
| H4 open-source model | `agx64` provider and public gateway; 32 models discovered | Done: Cloud verified 2026-11-17 |
| H5 LLM judge | opt-in structured judge; default off | Done: mocked |

The public gateway at `https://real-life.dev/v1` returns 401 without a token and
200 with it; a thinking-model completion also passes. The Streamlit Cloud
configuration was verified on 2026-11-17: discovery returned the gateway models
and a `gemma4-2b-131k:latest` completion returned `READY`. A fresh browser
loaded the public app; `curl` still receives a non-browser 303 auth redirect.
The `real-life.dev` project card remains suspended.

## Evaluation criteria coverage

| Criterion | Where explained | Status |
|---|---|---|
| Different prompting techniques | `PROMPTS.md`; `PromptLibrary`; `EVALUATION.md` | Done |
| LLM settings and their effects | `USER_MANUAL.md`; sidebar help; `EVALUATION.md` | Done |
| User/system/assistant roles | `USER_MANUAL.md`; `PROMPTS.md` | Done |
| Different output types | `QuestionSet`, `AnswerEvaluation`, chat text; parse errors | Done |
| Works as intended | tests, AppTest, headless HTTP 200 | Done |
| Calls OpenRouter with correct parameters | mocked provider tests; capability-aware request | Done |
| Uses a front-end library | Streamlit UI | Done |
| Explains prompt/settings choices | `PROMPTS.md`; `USER_MANUAL.md`; `RESEARCH.md` | Done |
| Understands problems | `SECURITY.md`; `EVALUATION.md`; `README.md` limits | Done |
| Suggests improvements | `README.md`; `USER_MANUAL.md` future-improvements section | Done |

## Link coverage

External LMS link capture is **suspended by owner decision**. Labels are retained
for traceability; no further href collection or URL guessing.

| Link | Status | Sprint 1 relevance |
|---|---|---|
| Completing a Sprint, Submitting a Project and Scheduling Reviews | Captured in brief | Submission/review |
| Git and GitHub for Beginners | Suspended | Git workflow |
| OpenRouter Docs | Suspended | API, models, pricing |
| Claude or ChatGPT | External tool | Critique/experimentation |
| What is the OpenAI API? (DataCamp) | Suspended | API request shape |
| Streamlit YouTube Channel | Suspended | UI patterns |
| Five simple starter apps | Suspended | Ideation only |
| OpenRouter image-generation guide | Suspended; excluded task | Image generation |
| OpenRouter models endpoint | Known: `https://openrouter.ai/api/v1/models` | Pricing/model metadata |
| Turing College GitHub repository | Known; access blocked | Submission |

Suspended means no further action is taken on the link; the label remains in the
matrix so the gap is visible.

## What is still blocked

- The Turing College repository is not writable by the active `reallife-spark`
  account; the course mirror and reviewer access are blocked.
- The public Streamlit app is deployed and the OpenRouter live path was
  smoke-tested on 2026-11-17 (question set, evaluation, Coach, safety, cost,
  export, clear; no key visible). **Submit Project** and review scheduling are
  user-gated.
- The project `.env` is absent; the Cloud secret is configured and the public
  path passed, but local live runs still need the project `.env`.
- Unauthenticated access to the LMS page returns 404; the user-pasted text is
  the captured source.
