---
title: Interview Practice Coach — user manual
updated: 2026-11-19
sources:
  - 03_Sources/turing-college/interview-practice-app-brief-2026-11-16.md
  - 06_Projects/interview-practice-app/README.md
  - 06_Projects/interview-practice-app/RESEARCH.md
tags:
  - user-manual
  - interview-practice
  - streamlit
  - openrouter
---

# Interview Practice Coach — user manual

## 1. What this app is

Interview Practice Coach is a single-page Streamlit workspace for AI-engineering
interview preparation. It has three surfaces:

- **Prepare** — generate role-specific interview questions.
- **Practice** — write an answer and get structured feedback.
- **Coach** — hold a multi-turn coaching conversation.

It is a practice aid, not a hiring decision, a personality test, or a
replacement for a human mock interview. The score is a coaching heuristic.

## 2. Who it is for

- Learners preparing for AI-engineering interviews.
- Candidates tailoring preparation to a specific job description.
- Reviewers who want to see prompt techniques, model settings, structured
  output and defensive prompting in one app.

## 3. Quick start

### Requirements

- Python 3.11 or newer.
- `pip` and a terminal.
- An OpenRouter API key for the normal/public mode; optional only for the
  developer offline mode.

### Install

```bash
cd /path/to/interview-practice-app
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Add the key for OpenRouter mode:

```text
OPENROUTER_API_KEY=your-key-here
OPENROUTER_MODEL=openai/gpt-6-luna
```

Never commit `.env`. It is gitignored. The app loads `.env` automatically.
The developer-only Demo mode works without a key when `PROVIDER=demo` is set.

### Run

```bash
streamlit run app.py
```

Open `http://localhost:8501`.

### Check the project

```bash
./scripts/check.sh
```

This runs tests, Ruff and the import-boundary gate.

## 4. Modes

| Mode | Network | Key | What it does |
|---|---|---|---|
| **Demo** | None | None | Developer-only with `PROVIDER=demo`; deterministic fixtures; no cost |
| **OpenRouter** | Yes | Required | Normal/public mode; live model calls through OpenRouter |
| **agx64** | Public HTTPS gateway | Gateway token | Open-source model path through `real-life.dev/v1` |

The mode is selected with the single **Model** selector under
**Settings → Developer settings**. It lists the three OpenRouter course models
and any discovered `agx64` models. Demo appears only when `PROVIDER=demo` is
explicitly set. Click **Discover agx64 models** to refresh the list from the
configured gateway first; the selector then includes the `agx64` options.

Without an OpenRouter key or explicit `PROVIDER=demo`, the app reports the
missing key instead of silently using the demo fixtures.

There is **no silent fallback** from local mode to OpenRouter. If a local call
fails, the app reports the failure; it does not send a private job description
to a remote provider.

## 5. First session

1. Add `OPENROUTER_API_KEY` to `.env`, or start the app with `PROVIDER=demo`
   for the offline developer mode.
2. Enter a target role, such as `AI engineer`.
3. Optionally paste a job description.
4. Choose a difficulty and number of questions.
5. Click **Generate question set**.
6. Open **Practice**, choose a question, write an answer and click
   **Evaluate answer**. The selector uses short `q1`-style labels; the full
   selected question is shown in a bordered panel above the answer box.
7. Open **Coach**, choose an interviewer style and ask a follow-up question.

## Optional features

| Feature | How to use | Cost / safety |
|---|---|---|
| Interview rubric | **Prepare → Generate interview rubric** | One model call |
| Excel red-team report | Developer settings → **Build jailbreak report**, or `python scripts/jailbreak_report.py --demo` | No network; formula cells sanitised |
| Question memory | Enable Chroma; generated questions only | Local `.chroma`; provider-scoped; instance-local on Streamlit Cloud |
| LangChain runtime | Select `langchain`; OpenRouter only | Optional dependency; native default |
| LLM judge | Enable; then **Run LLM judge** after an evaluation | Extra cost; default off |
| Parameter comparison | `python scripts/compare_settings.py --demo` | Deterministic; `--live` optional |

The public `agx64` path uses `LOCAL_BASE_URL=https://real-life.dev/v1` and the
server-side `LOCAL_API_KEY`. The gateway exposes only health, models, chat and
embeddings; it is not a general proxy.

## 6. Screen tour

### Sidebar

- **Model** — one selector for the three OpenRouter course models and discovered
  `agx64` models. Demo appears only with `PROVIDER=demo`. Choosing `agx64` never
  falls back to OpenRouter.
- **Discover agx64 models** — lazy refresh of the local model list from the
  configured gateway.
- **Prompt technique** — the six prompt variants.
- **Temperature**, **Max output tokens**, **Top-p** — model settings.
- **Reasoning effort** — available in OpenRouter mode.
- **Strict safety** — block known injection patterns instead of warning.
- **Lexical RAG-lite** — select relevant job-description chunks.
- **Refresh OpenRouter prices** — fetch current model metadata and prices.
- **Clear session** — reset questions, feedback, chat, budget and canary.
- **Generate interview rubric** — structured criteria and weights in Prepare.

### Prepare tab

- **Target role** — the role you are preparing for.
- **Job description** — optional; treated as data, never as instructions.
- **Difficulty** — easy, medium or hard.
- **Questions** — three to eight questions.
- **Generate question set** — one model call.

The result shows each question, category, difficulty, rationale and suggested
answer points. The raw `QuestionSet` JSON is available in an expander.

### Practice tab

- **Question** — choose from the generated set.
- **Your answer** — write the answer you would give.
- **Evaluate answer** — one structured model call.

The result shows score, summary, strengths, gaps, improved answer, next steps
and raw `AnswerEvaluation` JSON. If **LLM judge** is enabled, **Run LLM judge**
adds a separate structured score; it is not the same as the first-pass score.

### Coach tab

- **Interviewer style** — strict, neutral or friendly.
- **Chat input** — ask a follow-up question.
- **History** — session-only messages.
- **Export chat (Markdown/JSON)** — download the current session.

Chat history is not saved to disk.

## 7. Developer settings reference

| Setting | Default | What it changes | Practical guidance |
|---|---|---|---|
| Model | OpenRouter `openai/gpt-6-luna` | Provider and model in one choice | OpenRouter for live calls; `agx64` for the local path; Demo only with `PROVIDER=demo` |
| OpenRouter model | `openai/gpt-6-luna` | Model quality, speed and price | Start with the recommended default |
| Discover agx64 models | n/a | Refreshes the local model list | Run once after the gateway is up |
| Prompt technique | JSON schema | How the prompt is structured | JSON schema for reliable parsing; other techniques for comparison |
| Temperature | 0.7 | Randomness | Lower for consistent questions; higher for variety |
| Hard output cap | 1,200 | Hard provider stop, not an answer-length control | Raise for detailed structured JSON; use **Response style** for shorter answers. Low values can truncate JSON |
| Top-p | 1.0 | Nucleus sampling | Usually leave at 1.0 |
| Reasoning effort | none | Reasoning budget when supported | Use only when the model advertises it; high uses more of the output budget |
| Strict safety | off | Blocks known injection patterns | Turn on for a harder security demo |
| Hybrid RAG-lite | off | Selects job-description chunks with BM25 + hashed vectors + RRF | Turn on for long job descriptions |
| Session call cap | 20 | Model calls per session | Protects against repeated calls |
| Session cost cap | $0.50 | Estimated spend per session | Protects against cost abuse |
| Input cap | 8,000 chars | Maximum input length | Keeps prompts bounded |

Reducing the hard cap does not by itself make each answer shorter; it can cut a
JSON object mid-field. The app adds a budget hint to structured prompts, and a
truncated response now reports the cap explicitly. Use **Response style** or
reduce the question count instead of lowering the cap alone.

## 8. Prompt techniques

| Technique | Best for | Watch out for |
|---|---|---|
| Zero-shot | A clean baseline | May be shallow |
| Role / persona | Hiring-manager realism | Can become theatrical |
| Few-shot | Output shape and granularity | Examples may leak into content |
| Chain-of-thought | Trade-off reasoning | More tokens; hidden reasoning is not exposed |
| JSON schema | Reliable structured output | Shape can be correct but shallow |
| Prompt chaining | Long job descriptions and explicit requirements | Two calls; more cost and latency |

The defensive system prompt is always applied around the selected technique.
`PROMPTS.md` has the full prompt library.

## 9. Model roles and output types

The app uses three roles:

- **System** — the defensive interview-coach rules and selected technique.
- **User** — your role, job description, answer or chat message.
- **Assistant** — the model’s reply.

The app produces two output types:

1. **Text** — used by the Coach tab.
2. **Structured JSON** — `QuestionSet` and `AnswerEvaluation`.

If JSON is malformed or missing keys, the app shows a recoverable error. It does
not invent a result. If a model does not support JSON mode, the prompt still
asks for JSON and the parser handles the reply.

## 10. Cost, tokens and limits

- The app shows the session call count and session cost.
- The last call shows model, input/output tokens, latency and cost.
- OpenRouter pricing comes from the models endpoint and is loaded when
  OpenRouter mode is selected. Use **Refresh OpenRouter prices** to retry.
- Model metadata shows context length and whether JSON mode/reasoning are
  supported.
- The developer demo mode is $0.
- Local mode has no model charge, but your local hardware does the work.
- Session caps are application limits, not a billing guarantee.

## 11. Safety behaviour

- Job descriptions, answers and chat messages are **data**, not instructions.
- Off-topic requests should be politely declined and redirected by the
  defensive system prompt.
- Prompt-injection attempts are flagged by the rule detector; soft mode warns,
  strict mode blocks.
- Secret-shaped input is blocked and redacted.
- A per-session canary detects prompt leakage.
- The app never asks for passwords, keys or tokens.

If a request is blocked, rephrase it as interview preparation. If a model reply
is blocked, try again in soft mode or clear the session.

## 12. Privacy and data

- The developer demo mode makes no network calls.
- OpenRouter mode sends the prompt and job description to OpenRouter.
- Local mode sends them to the local endpoint.
- Chat history is in memory only.
- Export is explicit and downloads the current session.
- No secret should be pasted into the app.
- No analytics or telemetry is added by this project.

## 13. Troubleshooting

| Problem | Check |
|---|---|
| `OPENROUTER_API_KEY is required` | Add the key to `.env` or Streamlit secrets |
| `OpenRouter request failed (401)` | Key is invalid or lacks access |
| `OpenRouter request failed (429)` | Rate limit; wait or reduce calls |
| Price shows `unavailable` | Click **Refresh OpenRouter prices**; the model may not expose pricing |
| JSON parse error | Switch to **JSON schema**, retry, or check the model output |
| `invalid rubric` after retry | The error names the failed check; raise **Max output tokens** or switch models. The app retries once automatically |
| Output cap reached | Raise **Max output tokens** or reduce the number of questions/answer points; the cap is a hard stop, not a length setting |
| Question memory fails | Memory is optional; the app warns and continues. Check `EMBEDDING_MODEL` and the provider key. On Streamlit Cloud `.chroma` is instance-local and resets on redeploy |
| High reasoning error | The model may not support it; the app retries once without reasoning and shows a warning. Choose medium/none or raise the Hard output cap |
| `canary leaked in output` | The model revealed the exact session token; clear the session. A benign mention of the word "canary" no longer triggers this warning |
| `agx64` fails | Check the public gateway and `LOCAL_BASE_URL`; the older SSH tunnel is `http://127.0.0.1:21464/v1` |
| Cloud cannot reach `agx64` | Check `LOCAL_BASE_URL` and `LOCAL_API_KEY` in Streamlit secrets; gateways return 401/200 |
| Local thinking model returns empty content | The reasoning used the output cap; use a non-thinking model such as `gemma4-2b-131k:latest`, or raise **Max output tokens** |
| Session cap reached | Clear the session, or start with `PROVIDER=demo` for offline use |
| Clear session does not reset | Refresh the browser; session state is in memory |

## 14. Reviewer demo

Use `DEMO.md` for the five-minute script. The short version:

1. Start with `PROVIDER=demo`, then generate a question set.
2. Switch prompt technique and compare.
3. Practice an answer and show the structured feedback.
4. Try an off-topic question; expect a polite redirect.
5. Try an injection; show soft warning and strict block.
6. Show chat history and export.
7. Show model settings and cost.

## 15. Limitations

- The offline evaluation is a fixture, not a live model-quality result.
- The evaluation score is a coaching heuristic.
- Rule-based guardrails can miss paraphrased attacks.
- The RAG-lite path is hybrid and in-memory; it is not a vector database.
- The image-generation module is retained in the repository for future or
  external use; it is not exposed in the UI and is not part of the normal flow.
- Local mode is a developer path, not a public deployment.
- No live evaluation or deployment is claimed from the development host.

## 16. Future improvements

- Live prompt-quality evaluation with a dated run.
- Full vector-database retrieval in Sprint 2.
- More interviewer personas and drills.
- Streaming responses and per-call traces.
- Calibrated human review of the evaluation rubric.

## 17. Glossary

- **System prompt** — instructions that define the assistant’s role and rules.
- **User message** — the learner’s input.
- **Assistant message** — the model’s reply.
- **Structured output** — JSON with a known schema.
- **RAG** — retrieval-augmented generation; here, a lightweight local retrieval
  aid, not a vector database.
- **Canary** — a random token used to detect prompt leakage.
- **Soft mode** — warn on a detected injection pattern and continue.
- **Strict mode** — block a detected injection pattern.
- **Session** — the in-memory state until you clear or refresh.
