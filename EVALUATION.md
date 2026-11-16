---
title: Prompt evaluation — Interview Practice App
updated: 2026-11-17
sources:
  - 06_Projects/interview-practice-app/PROMPTS.md
  - eval/results.csv
  - eval/summary.md
tags:
  - evaluation
  - prompt-engineering
  - interview-practice
---

# Prompt evaluation

## Question

Which of the six prompt techniques produces the most useful question set for
the same three interview-preparation cases?

## Cases

Each technique is run on:

1. **RAG evaluation** — retrieval, grounding, latency, cost and regression
   gates.
2. **Behavioural collaboration** — trade-offs, feedback, stakeholder context
   and ambiguity.
3. **Senior system design** — versioning, safety, cost, rollback and
   evaluation.

Every case requests three questions at a fixed difficulty. Each case also names
expected concepts that a useful question set should cover.

## Rubric

The score is a combination of two axes:

- **Shape (50%)** — category coverage (30%), answer-point specificity (30%),
  difficulty match (15%), question length (15%) and requested count (10%).
- **Concept coverage (50%)** — how many of the case's expected concepts appear
  in the questions, rationale or answer points.

The score is out of 10. It checks structure and expected-content coverage, not
whether a human interviewer would rate the question highly. A live run can be
inspected manually; an LLM judge is not used as ground truth.

## Offline demo result

Prompt version: **2026-11-16**. Command:

```bash
python scripts/evaluate_prompts.py --demo
```

Outputs: `eval/results.csv`, `eval/summary.md`.

| Rank | Technique | Average / 10 |
|---:|---|---:|
| 1 | `json_schema` | 9.62 |
| 2 | `role_persona` | 8.79 |
| 3 | `few_shot` | 8.79 |
| 4 | `cot` | 8.79 |
| 5 | `chained` | 7.37 |
| 6 | `zero_shot` | 5.42 |

**Best in the offline fixture:** `json_schema`.

This is **not** a live model-quality result. The offline run uses a
deterministic scripted provider so the parser, guardrails, budget and scoring
path can be tested without a key. The fixture deliberately gives the schema
variant more expected concepts and answer points; it proves the harness and
rubric run, not that the live model behaves the same way.

## Live run

With an OpenRouter key available:

```bash
python scripts/evaluate_prompts.py --live --model openai/gpt-6-luna
```

Outputs are written to `eval/results.live.csv` and `eval/summary.live.md`.
They are gitignored. A live result must record its model, date, prompt version
and actual rows; it is a small sample, not a general benchmark. No live key was
available for this run.

## Interpretation

- Use `json_schema` as the default because it gives the parser a stable shape.
- Keep the other techniques selectable for comparison and review demos.
- Treat `zero_shot` as the baseline, not the production default.
- Re-run the live evaluation before making a quantitative claim.

## Limits

- Three cases is a small sample.
- Concept coverage is lexical, not semantic judgment.
- The rubric does not measure factual correctness or interview quality.
- The scripted demo cannot reveal model-specific behavior.
- A live run may be limited by budget, model availability and latency.
