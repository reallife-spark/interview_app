---
title: Turing College Sprint 1 — compliance map
updated: 2026-11-16
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
| Research the interview-preparation domain | `RESEARCH.md`; `BRIEF.md` domain choice | Will be complete in Phase 12 Step 82 |
| Single-page front-end using Streamlit | `app.py`; three tabs; `ui/_lib/layout.py` | Done |
| Call OpenRouter | `providers/_lib/openrouter.py`; `Provider.complete(CompletionRequest)` | Done; live key unavailable |
| Use a course-allowed model | default `openai/gpt-6-luna`; three-model chooser | Done |
| At least 5 system prompts with different techniques | six techniques in `PromptLibrary`; `PROMPTS.md` | Done |
| Check which prompt works best | `scripts/evaluate_prompts.py`; `EVALUATION.md`; offline fixture; live user-gated | Partial |
| Defensive system prompt | `prompts/_lib/defensive.py`; `GuardrailPipeline`; `SECURITY.md` | Done |
| Off-topic demo | `DEMO.md`; prompt-level tests in Phase 12 Step 87 | Manual/partial |
| Prompt-injection demo | red-team fixtures; `DEMO.md`; strict mode | Done |
| UI for a real interview-preparation experience | Prepare / Practice / Coach; `AppTest` | Done |
| Reflection and improvement | `README.md` limitations; `USER_MANUAL.md`; `RESEARCH.md` | Will be complete in Phase 12 |

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
| Assessment via LLM-as-judge or other | deterministic offline rubric; live run user-gated | Partial; no judge score claimed |

Excluded by scope decision: image generation, Excel jailbreak report, LangChain,
vector database, open-source-only model. These are not unfinished tasks.

## Evaluation criteria coverage

| Criterion | Where explained | Status |
|---|---|---|
| Different prompting techniques | `PROMPTS.md`; `PromptLibrary`; `EVALUATION.md` | Done |
| LLM settings and their effects | `USER_MANUAL.md`; sidebar help; `EVALUATION.md` | Complete after Step 82 |
| User/system/assistant roles | `USER_MANUAL.md`; `PROMPTS.md` | Complete after Step 82 |
| Different output types | `QuestionSet`, `AnswerEvaluation`, chat text; parse errors | Done; explain in Step 82 |
| Works as intended | tests, AppTest, headless HTTP 200 | Done |
| Calls OpenRouter with correct parameters | mocked provider tests; capability-aware request in Step 84 | Partial until Step 84 |
| Uses a front-end library | Streamlit UI | Done |
| Explains prompt/settings choices | `PROMPTS.md`; `USER_MANUAL.md`; `RESEARCH.md` | Complete after Step 82 |
| Understands problems | `SECURITY.md`; `EVALUATION.md`; `README.md` limits | Done |
| Suggests improvements | `README.md`; `USER_MANUAL.md` future-improvements section | Complete after Step 82 |

## Link coverage

The LMS page exposes labels but not hrefs. Exact unexposed URLs are marked
`needs LMS href`; no URL is guessed.

| Link | Status | Sprint 1 relevance |
|---|---|---|
| Completing a Sprint, Submitting a Project and Scheduling Reviews | Captured in brief | Submission/review |
| Git and GitHub for Beginners | Needs LMS href | Git workflow |
| OpenRouter Docs | Needs LMS href | API, models, pricing |
| Claude or ChatGPT | External tool | Critique/experimentation |
| What is the OpenAI API? (DataCamp) | Needs LMS href | API request shape |
| Streamlit YouTube Channel | Needs LMS href | UI patterns |
| Five simple starter apps | Needs LMS href | Ideation only |
| OpenRouter image-generation guide | Needs LMS href; excluded task | Image generation |
| OpenRouter models endpoint | Known: `https://openrouter.ai/api/v1/models` | Pricing/model metadata |
| Turing College GitHub repository | Known; access blocked | Submission |

## What is still blocked

- The Turing College repository is not writable by the active `reallife-spark`
  account; the course mirror and reviewer access are blocked.
- Streamlit Cloud deployment, **Submit Project** and review scheduling are
  user-gated.
- A live prompt-quality evaluation requires an OpenRouter key; no key is
  available at this time.
- Unauthenticated access to the LMS page returns 404; the user-pasted text is
  the captured source.
