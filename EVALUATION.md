---
title: Prompt evaluation — Interview Practice App
updated: 2026-11-16
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

1. **RAG evaluation** — an AI engineer must evaluate retrieval quality,
   grounding, latency, cost and regression gates.
2. **Behavioural collaboration** — an AI engineer must explain trade-offs,
   handle ambiguity and improve the team's evaluation practice.
3. **Senior system design** — design a prompt-evaluation pipeline with
   versioning, safety, cost and rollback.

Every case requests three questions at a fixed difficulty.

## Rubric

The deterministic rubric scores each question set out of 10:

| Component | Weight | Check |
|---|---:|---|
| Coverage | 30% | Distinct categories among technical, behavioural, system-design, role-specific and closing; four categories score full marks |
| Specificity | 30% | Average answer points per question, capped at three |
| Difficulty match | 15% | Every question matches the requested difficulty |
| Question length | 15% | Every question is at least 40 characters |
| Count match | 10% | The requested number of questions is present |

This is a **shape and pipeline** check. It does not measure whether a question
would impress a human interviewer. A live run can be inspected manually; an
LLM judge is deliberately out of scope for the selected bonus tasks.

## Offline demo result

Command:

```bash
python scripts/evaluate_prompts.py --demo
```

Outputs: `eval/results.csv`, `eval/summary.md`.

| Rank | Technique | Average / 10 |
|---:|---|---:|
| 1 | `json_schema` | 9.25 |
| 2 | `role_persona` | 8.25 |
| 3 | `few_shot` | 8.25 |
| 4 | `cot` | 8.25 |
| 5 | `chained` | 8.25 |
| 6 | `zero_shot` | 6.50 |

**Best in the offline fixture:** `json_schema`.

This is **not** a live model-quality result. The offline run uses a deterministic
scripted provider so the parser, guardrails, budget and scoring path can be
tested without a key. The fixture gives the schema variant more categories and
answer points by design; it proves the harness runs, not that the live model
behaves the same way.

## Live run

With an OpenRouter key available in the environment:

```bash
python scripts/evaluate_prompts.py --live --model openai/gpt-6-luna
```

Outputs are written to `eval/results.live.csv` and `eval/summary.live.md`.
They are gitignored. A live result must record its model, date and actual rows;
it is a small sample, not a general benchmark.

## Interpretation

- Use `json_schema` as the default because it gives the parser a stable shape.
- Keep `role_persona`, `few_shot`, `cot` and `chained` selectable for review
  demos and for comparing prompt styles.
- Treat `zero_shot` as the baseline, not the production default.
- Re-run the live evaluation before making a quantitative claim; the offline
  table is a fixture result.

## Limits

- Three cases is a small sample.
- The rubric rewards structure and specificity, not factual correctness.
- The scripted demo cannot reveal model-specific behavior.
- A live run may be limited by budget, model availability and latency.
