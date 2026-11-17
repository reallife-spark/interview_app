---
title: Application critique — Interview Practice App
updated: 2026-11-17
sources:
  - src/interview_practice
  - tests
  - USER_MANUAL.md
tags:
  - review
  - security
  - usability
---

# Application critique

This is an **LLM code and usability review**, not an external security audit.
It records what was checked, what changed and what remains user-gated.

## Findings and disposition

| Area | Finding | Disposition |
|---|---|---|
| Secret handling | The Cloud key was pasted in chat; local `.env` loading was documented but absent. | Project `.env` loading exists; key rotation is owner action. No key is written here. |
| Secret coercion | Numeric and boolean Streamlit secrets were ignored. | Fixed: `apply_secret_values()` coerces supported values. |
| Cost abuse | Per-session caps could be bypassed across sessions. | Fixed: process-wide daily/rate/cost guard; OpenRouter account limit remains the hard stop. |
| Provider reliability | OpenRouter calls had no bounded retry and catalog parsing accepted malformed values. | Fixed: bounded 429/network/5xx retries and strict catalog validation. |
| Context continuity | Coach lost the job description after the first turn and lacked the current question/evaluation. | Fixed: JD, current question and current evaluation are carried into the chat prompt. |
| Model selection | Provider and model were split across controls; local discovery was not user-visible. | Fixed: one Model selector with Demo, OpenRouter and discovered `agx64` options. |
| Fallback | A local failure could be mistaken for a remote success. | Explicit no-fallback rule; local errors stay local. |
| Prompt safety | The defensive layer must remain first and last in every call. | Added runtime system-prompt integrity checks and field caps. |
| Input bounds | One global cap covered all fields; role and answer had no tighter bound. | Added role 120, question 500, answer/chat 4000 character caps plus the global cap. |
| Accessibility | The single-page layout has clear labels and captions, but no automated WCAG audit was run. | Not verified here; manual browser review remains. |
| Image generation | Optional image calls can create cost and abuse risk. | Keep opt-in, one image per action, OpenRouter-only and hidden for Demo/`agx64`. |
| `agx64` exposure | A home endpoint cannot be exposed directly. | Public HTTPS gateway with bearer token, rate limit and WireGuard; no direct `11434`. |
| Documentation | Token-budget and deployment-status text drifted. | Reconcile in `REQUIREMENTS.md`, `SECURITY.md`, `README.md` and `COURSE_COMPLIANCE.md`. |

## Boundaries

- No external penetration test, WCAG audit or live Streamlit Cloud secret check is
  claimed.
- Mocked provider tests do not prove a live model's quality.
- The `real-life.dev` project card remains suspended; the gateway is
  infrastructure, not a card.
