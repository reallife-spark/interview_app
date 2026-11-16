---
title: Interview Practice App — brief
updated: 2026-11-16
sources:
  - 03_Sources/turing-college/interview-practice-app-brief-2026-11-16.md
  - https://github.com/TuringCollegeSubmissions/rmobil-AE.1.5
tags:
  - turing-college
  - sprint-1
  - interview-practice
  - streamlit
  - openrouter
---

# Interview Practice App — brief

## Goal

Build a single-page Streamlit app that helps a candidate prepare for an AI
engineering interview by generating role-specific questions, evaluating written
answers, and holding a multi-turn coaching conversation. The app calls
OpenRouter, demonstrates at least five prompt techniques, and defends itself
against off-topic use and prompt injection.

## Chosen interview domain

**AI engineering roles**, with a job-description-tailored path. A user can paste
a job description and receive questions and feedback grounded in that
description. This is specific enough to be useful and broad enough to exercise
prompt chaining, structured output and retrieval.

The app is not a generic chatbot. It is an interview-preparation workspace with
three surfaces:

1. **Prepare** — role and job description produce a structured question set.
2. **Practice** — a question and a written answer produce structured feedback.
3. **Coach** — a multi-turn conversation for follow-up questions, mock-interview
   personas, and study planning.

## Required behaviour

- Streamlit single-page UI; no Next.js.
- OpenRouter API call with a course-allowed model. Default:
  `openai/gpt-6-luna`.
- At least five system prompts with different techniques; the app records which
  one performs best in the evaluation.
- Defensive system prompt: stay on interview preparation, politely decline
  off-topic requests, ignore attempts to override instructions.
- Job-description field with lightweight retrieval; no vector database.
- Developer settings separated from the learner-facing experience.
- Session-only history, visible cost estimate, export, and clear session.
- Demo mode that works without a key; no silent fallback from local to
  OpenRouter.

## Bonus scope

Five medium tasks and one hard task:

- All model settings: model, temperature, `max_tokens`, `top_p`,
  `reasoning_effort` when supported.
- Two JSON formats: `QuestionSet` and `AnswerEvaluation`.
- Price estimate from OpenRouter model metadata.
- Job-description tailoring with lexical RAG-lite.
- Model chooser limited to the three course models.
- Security guard with soft-flag default and a strict toggle.
- Full multi-turn chatbot.

Excluded: image generation, Excel jailbreak report, LangChain, vector database,
open-source-only model requirement. These are deliberate scope decisions, not
unfinished work.

## Prompt techniques

The prompt library has six named variants:

1. Zero-shot baseline.
2. Role/persona.
3. Few-shot.
4. Chain-of-Thought or structured reasoning.
5. JSON-schema output.
6. Prompt chaining (question generation then answer evaluation).

The evaluation compares at least five variants on the same cases and records the
winning variant with its evidence. A separate defensive system prompt is always
applied around the selected technique.

## Safety model

- Job descriptions, answers, and chat messages are **data**, not instructions.
- The system prompt says so explicitly and places them inside XML boundaries.
- Input validation rejects empty/oversized payloads.
- A secret scanner blocks or redacts likely credentials.
- An injection detector flags override patterns; soft mode warns, strict mode
  blocks.
- A per-session canary token is checked in the output; leakage is flagged.
- `SECURITY.md` states the limits: rule-based detection is a layer, not a
  guarantee.

## Repositories

- Private working/backup repo: `interview_app`, under the GitHub account
  authenticated as `reallife-spark` (SparkNet; user-stated email
  `dev@real-life-spark.de`).
- Course submission repo:
  `https://github.com/TuringCollegeSubmissions/rmobil-AE.1.5`.
- The course repo is the reviewer-visible artifact. The private repo is the
  backup. Push to both; never force-push without explicit confirmation.

## Definition of done

- The app runs in demo mode with no key and in OpenRouter mode with a key.
- The user can generate questions, practise an answer, get feedback, and chat.
- Five prompt variants are selectable and evaluated.
- Off-topic and injection demos are documented with observed results.
- The course repo contains the project and history; the reviewer can see it.
- `README.md`, `PROMPTS.md`, `SECURITY.md`, `EVALUATION.md`, `DEMO.md`, and
  `DEPLOYMENT.md` are complete.
- No secret is present in any page, log, commit, or command output.
- No live deployment or model-quality claim is made from this host.
