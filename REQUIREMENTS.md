---
title: Interview Practice App — requirements matrix
updated: 2026-11-17
sources:
  - 03_Sources/turing-college/interview-practice-app-brief-2026-11-16.md
  - 06_Projects/interview-practice-app/BRIEF.md
tags:
  - turing-college
  - sprint-1
  - requirements
---

# Interview Practice App — requirements matrix

Status values: `planned`, `in-progress`, `partial`, `done`, `excluded`, `blocked`.
A requirement is `done` only after its check passes.

## Core requirements

| ID | Requirement | Implementation | Verification | Status |
|---|---|---|---|---|
| R1 | Single-page Streamlit app | `app.py` with three tabs | `AppTest` smoke test | done |
| R2 | OpenRouter API call | `providers/_lib/openrouter.py`; `/chat/completions` | mocked HTTP test | done |
| R3 | Course-allowed model | default `openai/gpt-6-luna`; chooser limited to the three listed models | config test | done |
| R4 | At least five system prompts with different techniques | six techniques behind `PromptLibrary` | prompt tests + `PROMPTS.md` | done |
| R5 | Check which prompt works best | `scripts/evaluate_prompts.py` + `EVALUATION.md` | demo + dated live sample | done |
| R6 | Defensive system prompt | `prompts/_lib/defensive.py`; `guardrails.py`; stay-on-topic/ignore-override instructions | red-team fixtures | done |
| R7 | Off-topic and injection demo | `scripts/red_team_prompts.py`; `DEMO.md`; prompt-level tests | demo output captured | done: prompt-level + manual demo |
| R8 | Real interview-preparation experience | Prepare, Practice, Coach flows | `AppTest` flow assertions | done |
| R9 | Job-description field | `tailoring.py`; `<JobDescription>` XML boundary | tailoring tests | done |
| R10 | Session-only chat history | `session.py`; no persistence | clear/export tests | done |
| R11 | Export and clear session | Markdown/JSON export; clear button | `AppTest` test | done |
| R12 | Demo mode | deterministic fixtures; default when no key | provider test | done |
| R13 | Local `agx64` mode | OpenAI-compatible provider; public gateway `https://real-life.dev/v1`; auto-detect `/v1/models` | mocked local test; public 401/200, Cloud discovery and completion on 2026-11-17 | done: gateway and Cloud secret verified |
| R14 | No silent provider fallback | provider selected explicitly; local failure stays local | provider test | done |
| R15 | Cost visibility | OpenRouter model metadata + token usage; per-call and session | cost tests | done |
| R16 | Model settings | model, temperature, `max_tokens`, `top_p`, `reasoning_effort` when supported | UI/config tests | done |
| R17 | Two structured JSON formats | `QuestionSet`, `AnswerEvaluation` schemas + parser | schema tests | done |
| R18 | Security guard | input validation, secret scan, injection detection, canary, strict toggle | guardrail tests | done |
| R19 | Developer settings separated from learner UX | sidebar “Developer settings” expander | `AppTest` test | done |
| R20 | README and run instructions | `README.md` | quickstart read-through | done |
| R21 | Prompt documentation | `PROMPTS.md` | technique coverage check | done |
| R22 | Security documentation | `SECURITY.md` | OWASP mapping and limitations | done |
| R23 | Evaluation documentation | `EVALUATION.md`; `eval/results.csv`; `eval/summary.md` | demo/live result recorded | done: offline; live user-gated |
| R24 | Deployment documentation | `DEPLOYMENT.md`; Streamlit secrets | public app live; OpenRouter smoke 2026-11-17 | done |
| R25 | Course repo submission | `course` remote; push to `rmobil-AE.1.5` | user checks GitHub page | blocked: 403/404; active account `reallife-spark` vs alias `rmobil` |
| R26 | Private backup repo | `interview_app` under `reallife-spark`; branch `feat/optional-expansion`; tags `v0.1.1`, `v0.1.2-pre-optional` | `git status`/GitHub | done |
| R27 | No secrets in tracked content | `.gitignore`; `.env.example`; secret scan | `git grep`/scanner | done |
| R28 | No live claim from development host | docs use “implemented and tested” or “not verified here” | doc review | done |
| R29 | Deadline discipline | MVP first; optional tasks after required features | timeline check | done |
| R30 | Review scheduling | user submits and books review | user confirmation | planned: waits on course repo |
| R31 | User manual | `USER_MANUAL.md` | manual read-through | done |
| R32 | Research note | `RESEARCH.md` | research read-through | done |
| R33 | Course compliance map | `COURSE_COMPLIANCE.md` | source/status audit | done |

## Bonus requirements

| ID | Requirement | Implementation | Verification | Status |
|---|---|---|---|---|
| B1 | All model settings | sliders/fields in sidebar | UI test | done |
| B2 | Two JSON formats | `QuestionSet`, `AnswerEvaluation` | schema tests | done |
| B3 | Prompt price | `cost.py` + OpenRouter models endpoint | cost test | done |
| B4 | OpenRouter docs improvement | model catalog drives picker, pricing, context length, supported parameters | config test | done |
| B5 | Job-description tailoring (RAG) | whole-text v1 + hybrid RAG-lite (BM25 + hashed vectors + RRF) | tailoring test | done |
| B6 | LLM chooser | one selector: three course models + discovered `agx64` models | UI/config tests | done |
| B7 | Security guard | soft/strict modes | guardrail test | done |
| B8 | Full chatbot | Coach tab with history | chat test | done |
| B9 | Prompt/model evaluation | deterministic rubric; dated live sample | eval test | done |
| B10 | Interviewer personas | `PromptLibrary` persona layer; Coach selector | prompt/UI tests | done |

## Optional task matrix

All E/M/H tasks are implemented or explicitly evidenced. A mocked test is not a
live-model quality claim.

| ID | Optional task | Evidence | Status |
|---|---|---|---|
| E1 | LLM critique of usability, security and prompts | `APP_CRITIQUE.md` | done: LLM review, not external audit |
| E2 | Personal-domain prompt profiles | `prompts/domains.py`; domain tests | done |
| E3 | More security constraints / system-prompt validation | `prompts/integrity.py`; field caps; integrity tests | done |
| E4 | Difficulty levels | `Prepare` difficulty selector; question schema/tests | done |
| E5 | Concise vs detailed prompts | `prompts/styles.py`; style tests | done |
| E6 | Structured interviewer guidelines | `InterviewRubric` schema, engine and UI; rubric tests | done |
| E7 | AI personas | strict/neutral/friendly persona layer and Coach selector | done |
| E8 | Compare a model setting | `scripts/compare_settings.py --demo`; optional `--live` | done: deterministic demo |
| M1 | All model settings | model, temperature, max tokens, top-p, reasoning effort | done |
| M2 | Two structured JSON formats | `QuestionSet`, `AnswerEvaluation`, rubric and judge shapes | done |
| M3 | Prompt price | `cost.py`, OpenRouter catalog, usage/cost display | done |
| M4 | Original OpenRouter improvement | capability-aware catalog, pricing, model discovery and selector | done |
| M5 | Excel jailbreak report | `reports.py`; `scripts/jailbreak_report.py`; workbook download/test | done |
| M6 | Job-description tailoring (RAG) | `tailoring.py`; hybrid RAG-lite tests | done |
| M7 | LLM chooser | unified Model selector; three OpenRouter + `agx64` models | done |
| M8 | Image generation | `imagegen.py`; opt-in OpenRouter action; mocked image test | done: mocked; not live-tested |
| M9 | Security guard + developer settings separation | `guardrails.py`; Developer settings expander; tests | done |
| H1 | Full chatbot | Coach tab with session history | done |
| H2 | LangChain chains | `providers/_lib/langchain.py`; `CHAIN_RUNTIME=langchain`; importorskip test | done: mocked/native default |
| H3 | Vector database | `retrieval/` Chroma memory; provider-scoped collections; duplicate test | done: Chroma test; no live embedding claim |
| H4 | Open-source LLM | `agx64` local provider and public gateway; 32 models discovered | done: gateway and Cloud secret verified 2026-11-17 |
| H5 | LLM-as-judge | opt-in `judge_answer`; structured judge schema; engine test | done: mocked; default off |

## Originally excluded, now implemented

| ID | Requirement | Phase 16 disposition |
|---|---|---|
| X1 | Image generation | Implemented as opt-in M8; OpenRouter-only |
| X2 | Excel jailbreak report | Implemented as M5 with formula sanitisation |
| X3 | LangChain | Implemented as optional H2; native remains default |
| X4 | Vector database | Implemented as optional H3 Chroma question memory |
| X5 | Open-source-only model | Implemented through `agx64` H4 |

## User-gated checks

| ID | Check | Gate | Status |
|---|---|---|---|
| G1 | GitHub account is `reallife-spark` and is the intended account | `gh auth status` and `gh api user` checked; email scope unavailable | done |
| G2 | Private repo `interview_app` may be created | explicit user request; created | done |
| G3 | Course repo push | `git ls-remote` 403; `gh api`/`curl` 404; active account `reallife-spark` vs alias `rmobil` | blocked |
| G4 | Streamlit Cloud public access | Fresh browser loaded the app on 2026-11-17; followed auth chain ends at 200; first-hop 303 is anonymous bootstrap | done: public browser smoke |
| G5 | Review booked | user action; course mirror still blocked | planned |

## Course documents

- Task brief: `03_Sources/turing-college/interview-practice-app-brief-2026-11-16.md`.
- Course status and link ledger:
  `03_Sources/turing-college/sprint-1-course-status-2026-11-16.md`.
- Canonical LMS page:
  `https://intra.turingcollege.com/hardskills/build-an-interview-practice-app`
  (unauthenticated fetch returned 404 on 2026-11-16).
- External LMS link capture is suspended by owner decision; no hrefs are
  collected or guessed. See `COURSE_COMPLIANCE.md`.

## Evidence rules

- Offline tests prove code paths, not live model quality.
- A live OpenRouter run must record model, date, prompt variant and observed
  output; no aggregate claim beyond the sample.
- Local `agx64` checks prove that path only. The public gateway was verified
  from the build host on 2026-11-17; the Streamlit Cloud secret was verified
  by discovery and a completion on 2026-11-17.
- `03_Sources/` is read-only after capture.
