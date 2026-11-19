# Prompt evaluation

- Mode: **demo**
- Date: **2026-11-19**
- Model: **scripted/interview-fixture (offline fixture)**
- Cases: **3** per technique
- Techniques: **6**
- Prompt version: **2026-11-16**

## Ranking

| Rank | Technique | Average score / 10 | Valid rows |
|---:|---|---:|---:|
| 1 | json_schema | 9.62 | 3/3 |
| 2 | role_persona | 8.79 | 3/3 |
| 3 | few_shot | 8.79 | 3/3 |
| 4 | cot | 8.79 | 3/3 |
| 5 | chained | 7.37 | 3/3 |
| 6 | zero_shot | 5.42 | 3/3 |

**Best in this run:** `json_schema`

## Method

Each technique generated a question set for three cases: RAG evaluation,
behavioural collaboration, and a senior system-design prompt. The
score is 50% shape and 50% expected-concept coverage. Shape weights
category coverage (30%), answer-point specificity (30%), difficulty
match (15%), question length (15%) and requested count (10%). This is
a pipeline and content-coverage check, not a claim about the model's
general quality.

## Limitation

This is an **offline fixture run**. The scripted provider is designed
to exercise parsing, guardrails and scoring; it is not a live model
comparison. Run `python scripts/evaluate_prompts.py --live` with an
OpenRouter key for a dated live sample.
