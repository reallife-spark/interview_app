---
title: Security — Interview Practice App
updated: 2026-11-16
sources:
  - 03_Sources/turing-college/interview-practice-app-brief-2026-11-16.md
  - 03_Sources/ai-engineering/web/web-simon-willison-prompt-injection.md
  - 05_Knowledge/references/ai-engineering/web-simon-willison-prompt-injection.md
tags:
  - security
  - prompt-injection
  - guardrails
---

# Security

## Scope and threat model

The app has one public surface: a Streamlit page that sends interview
preparation text to an LLM. The assets to protect are the OpenRouter key, the
user's job description and answer, the system prompt, and the integrity of the
interview-preparation experience.

Threats considered:

1. **Prompt injection** in a job description, answer, or chat message.
2. **Off-topic misuse** that turns the coach into a general assistant.
3. **Secret leakage** into a model call, page, log, or export.
4. **System-prompt or canary leakage** in a model reply.
5. **Cost abuse** through repeated or oversized calls.
6. **Unsafe output handling** when parsing model JSON.

Out of scope: multi-user isolation, a public API, file uploads, tool execution,
browsing, and any offensive-security capability.

## Controls

| Control | Where | Behaviour |
|---|---|---|
| Defensive system prompt | `prompts/_lib/defensive.py` | Interview-only scope, data-not-instructions rule, refusal, canary |
| Input length/type validation | `guardrails.py` | Empty or oversized input is blocked |
| Secret scanner | `guardrails.py` | Common key/token shapes are blocked and redacted |
| Injection detector | `guardrails.py` | Known override, role-hijack and prompt-extraction patterns |
| Soft-flag default | `GuardrailPipeline(strict=False)` | Warn and continue |
| Strict toggle | sidebar | Block the flagged input or output |
| Canary | `session.py` + output check | Per-session random token; leakage is flagged and redacted |
| XML data boundaries | `prompts/_lib/templates.py` | Job description and answer are escaped inside data tags |
| JSON parser + schemas | `prompts/schemas.py` | Invalid JSON or missing keys becomes a recoverable error |
| Call cap | `session.py` | Default 20 calls per session |
| Cost cap | `session.py` | Default `$0.50` per session |
| Output cap | `session.py` / provider | Default 400 output tokens |
| No local fallback | `providers/__init__.py` | Local failure stays local; no private data leaves the host silently |
| Key handling | `config.py` + `.env.example` | Keys are `repr=False`, never written to the page |
| Red-team fixtures | `tests/fixtures/red_team.json` | Reproducible safe checks |

## Soft mode vs strict mode

- **Soft (default):** a known injection pattern produces a visible warning and
  the call continues. This keeps the review demo usable and shows the user what
  was detected.
- **Strict:** a known injection pattern blocks the call. The user sees a
  recoverable error. Secrets are blocked in both modes.

The toggle is in the **Developer settings** expander. The app does not hide
safety state from the learner.

## Canary

Each session gets a random `canary-...` token. It is included in the defensive
prompt with an instruction never to reveal it. The output guard checks for the
exact token:

- Soft mode: redact it, flag the warning, allow the rest of the response.
- Strict mode: block the output.

A canary leak is evidence that the model ignored a defensive instruction, not
proof of a broader compromise. Rotate the token by clearing the session.

## Secret handling

- The OpenRouter key comes from environment or Streamlit secrets.
- `.env` is gitignored; `.env.example` has placeholders only.
- The app never reads or echoes `.env` in the UI.
- The private secret scanner blocks common shapes, including OpenRouter, OpenAI
  and GitHub tokens, bearer tokens and credential assignments.
- The scanner is a layer, not a complete data-loss-prevention product.

## OWASP LLM Top 10 mapping

| Risk | This app |
|---|---|
| LLM01 Prompt Injection | Defensive prompt, XML boundaries, rule detector, red-team fixtures |
| LLM02 Insecure Output Handling | JSON parsing and schema validation; Streamlit escapes display |
| LLM03 Training Data Poisoning | Out of scope; no training data path |
| LLM04 Model Denial of Service | Call, input, output and cost caps; request timeouts |
| LLM05 Supply Chain | Pinned requirements; no runtime skill or plugin loading |
| LLM06 Sensitive Information Disclosure | Secret scanner, canary, no key logging |
| LLM07 Insecure Plugin Design | No plugins, tools, browsing or file access |
| LLM08 Excessive Agency | No external actions; the model only returns text or JSON |
| LLM09 Overreliance | Scores are labelled heuristic; evaluation limits documented |
| LLM10 Model Theft | Out of scope; no model weights are hosted |

The mapping is a design aid, not a certification.

## Red-team demo

Safe fixtures live in `tests/fixtures/red_team.json` and run offline:

```bash
python scripts/red_team_prompts.py --demo
```

| Case | Soft | Strict |
|---|---|---|
| Ignore previous instructions | warned | blocked |
| Reveal the system prompt | warned | blocked |
| Role hijack | warned | blocked |
| Injection in a job description | warned | blocked |
| Fake secret shape | blocked | blocked |
| Benign interview question | allowed | allowed |

For the review, also try an off-topic question such as “What is the weather?”
The defensive prompt should politely decline and redirect to interview
preparation.

## Residual risks

- A paraphrased injection can evade the rule detector.
- A model can ignore the defensive prompt; the canary only detects one class of
  failure.
- The public app trusts OpenRouter's availability and policy.
- The cost cap is an application limit, not a billing control.
- Session history is in memory only; a browser refresh loses it.
- The app does not authenticate users; public access is controlled by the
  deployment and spend caps, not by identity.

## Reporting

This is a course project. Report a security issue to the project owner rather
than publishing an exploit. Do not include keys, job descriptions, or personal
data in a report.
