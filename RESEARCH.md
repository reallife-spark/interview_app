---
title: Interview-preparation research — AI engineering
updated: 2026-11-16
sources:
  - 03_Sources/turing-college/interview-practice-app-brief-2026-11-16.md
  - 06_Projects/interview-practice-app/BRIEF.md
tags:
  - interview-preparation
  - research
  - ai-engineering
  - product-design
---

# Interview-preparation research — AI engineering

## Purpose

This is the design research behind the app’s chosen domain. It is a reasoned
domain map and set of product assumptions, not an empirical study of hiring
outcomes. The course asks the learner to research the nature of interview
preparation; this note records what the app prepares for and why.

## Chosen domain

**AI-engineering roles**, from mid-level application engineers to senior
engineers working on LLM products. The app focuses on:

- technical depth in Python, APIs, LLM orchestration, retrieval and evaluation;
- system design for LLM applications;
- behavioural and collaboration questions;
- job-description-specific preparation.

It is not a general coding-interview platform, a personality-test simulator, or
a replacement for a human mock interview.

## Typical interview loop

The app models a common five-stage loop:

1. **Recruiter or hiring-manager screen** — motivation, role fit, communication,
   basic technical background.
2. **Technical screen** — Python, APIs, data handling, debugging, LLM
   fundamentals.
3. **Applied or system-design round** — design a RAG service, evaluation
   pipeline, agent workflow or prompt system; discuss trade-offs, safety, cost
   and operations.
4. **Behavioural round** — collaboration, ambiguity, conflict, ownership,
   failure and learning.
5. **Closing conversation** — questions for the team, scope, expectations and
   next steps.

The app’s three surfaces map to this loop:

- **Prepare** — questions tailored to a role and job description.
- **Practice** — written answer and structured feedback.
- **Coach** — follow-up conversation, mock-interview style and study planning.

## Competency map

| Area | What a strong answer shows |
|---|---|
| Python and software engineering | Clear structure, tests, error handling, maintainability |
| LLM API use | Correct roles, parameters, structured output, retries and cost awareness |
| Prompt engineering | Explicit instructions, data/instruction separation, examples and output constraints |
| Retrieval and RAG | Chunking, retrieval quality, grounding, citation and failure analysis |
| Evaluation | Labelled cases, retrieval vs generation metrics, regression gates and human review |
| Safety | Prompt injection, secrets, data boundaries, least privilege and limitations |
| System design | Requirements, components, data flow, latency, cost, observability and rollback |
| Communication | Concise trade-offs, evidence, uncertainty and stakeholder framing |
| Ownership | Decisions, failures, learning and measurable outcomes |

## Question types

- **Technical** — “How would you evaluate a RAG system?”, “What happens when a
  retrieved document conflicts with the prompt?”
- **Behavioural** — “Tell me about a time you changed a design after user
  feedback.”
- **System design** — “Design a prompt-evaluation pipeline with versioning,
  safety, cost and rollback.”
- **Role-specific** — questions derived from the job description’s actual
  responsibilities and must-have skills.
- **Closing** — questions that test scope, team health and expectations.

## Answer structures

### STAR for behavioural answers

- **Situation** — the context and constraint.
- **Task** — the responsibility.
- **Action** — the specific decisions and trade-offs.
- **Result** — the measurable outcome and what changed.

### Trade-off structure for technical answers

1. Restate the goal and constraints.
2. Name the options.
3. Choose one and justify it.
4. State the failure mode and mitigation.
5. Name the metric that would prove the choice.

### System-design structure

1. Clarify users, scope and success criteria.
2. Sketch components and data flow.
3. Address retrieval, generation, safety, evaluation and cost.
4. Discuss failure modes and rollback.
5. State what you would measure first.

## Job-description analysis

The app treats a job description as data. It extracts signals such as:

- responsibilities and ownership level;
- must-have technical skills;
- nice-to-have or domain skills;
- seniority and collaboration expectations;
- likely interview themes.

The current implementation uses a bounded hybrid retrieval path: section-aware
chunking, BM25, deterministic hashed vectors and reciprocal-rank fusion. A long
job description is chunked and the most relevant chunks are selected. This is
deliberately not a vector database; it is a transparent, local retrieval aid.

## Practice loop

1. Choose a role and paste a job description.
2. Generate a question set with a prompt technique and difficulty.
3. Answer one question in writing.
4. Read the structured evaluation: score, strengths, gaps, improved answer and
   next steps.
5. Ask the coach for a follow-up drill or study plan.
6. Repeat with a different technique or difficulty.

## Assumptions and limits

- The app assumes the learner already knows the basics of Python and LLM APIs.
- A generated question is a practice prompt, not a real hiring decision.
- The evaluation score is a coaching heuristic, not a validated hiring rubric.
- The app does not know the user’s actual interview panel, company or level.
- The job-description path is retrieval-lite, not a full RAG system.
- No user study, hiring-outcome dataset or labour-market analysis was run.

## Related knowledge

- Prompt structure and data/instruction separation:
  [[05_Knowledge/references/ai-engineering/web-anthropic-prompt-engineering]]
- Retrieval and RAG architecture:
  [[06_Projects/ai-engineering/implementations/track-rag-retrieval]]
- Evaluation loop:
  [[06_Projects/ai-engineering/implementations/track-evaluation-observability]]
- Safety and prompt injection:
  [[06_Projects/ai-engineering/implementations/track-safety-security]]
