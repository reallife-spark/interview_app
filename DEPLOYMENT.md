---
title: Deployment and submission — Interview Practice App
updated: 2026-11-16
sources:
  - 03_Sources/turing-college/interview-practice-app-brief-2026-11-16.md
  - README.md
tags:
  - deployment
  - github
  - streamlit
  - turing-college
---

# Deployment and submission

## Repositories

| Purpose | Remote | Notes |
|---|---|---|
| Private working backup | `interview_app` under the authenticated GitHub account | Created by the owner or with explicit confirmation |
| Course submission | `https://github.com/TuringCollegeSubmissions/rmobil-AE.1.5` | Reviewer-visible; the course repo must contain the project |

The build agent must confirm `gh auth status` shows the intended account before
creating or pushing. Do not create the private repo under a different account.

**Current check (2026-11-16):** the private repo
`https://github.com/reallife-spark/interview_app` was created and `main` pushed
tagged `v0.1.1`. The `course` remote was added, but `git ls-remote course`
returned HTTP 403 (`Write access to repository not granted`); `gh api` and
`curl` both returned 404. The active `gh` account is `reallife-spark`, while the
repository alias is `rmobil`. The course mirror is blocked until the correct
student GitHub identity is active and the LMS GitHub URL is confirmed. See
`HANDOFF.md`.

**Deployment preflight (2026-11-17):** the project `.env` is absent. The vault
root has an `.env`, but this app intentionally loads only its own project
`.env`; the root file is not read. Add the rotated key to
`/mnt/knowledge/AIengin/06_Projects/interview-practice-app/.env` for local live
testing, or to Streamlit Cloud secrets for the public app. The public app is
live at
<https://interviewap-nbsnftcgrwj7yjcm2h658m.streamlit.app/>. The first preflight
render showed **Demo — no key**; the later public smoke loaded the OpenRouter
secret and passed.

## Local setup

```bash
cd /path/to/interview-practice-app
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Add the key to `.env` locally:

```text
OPENROUTER_API_KEY=your-key-here
OPENROUTER_MODEL=openai/gpt-6-luna
```

Never commit `.env`. The `.gitignore` already excludes it.

> Vault-specific note: if this project is inside AIengin, the vault's
> `scripts/validate.sh` scans secret-shaped files. Keep `.venv` outside the
> vault or remove it before running the validator. The validator now excludes
> `.venv` and `.git`, but other local caches may still need attention.

## Run locally

```bash
streamlit run app.py
```

Open `http://localhost:8501`. Demo mode is selected when no key is present.
OpenRouter mode requires the key and a course-allowed model.

## Pre-deployment checks

```bash
pytest -q
ruff check .
python scripts/evaluate_prompts.py --demo
python scripts/red_team_prompts.py --demo
```

Expected on this host (2026-11-17): 114 tests, Ruff 0, 18 evaluation rows,
red-team fixtures pass.

## Git: private repo and course mirror

### 1. Verify the account

```bash
gh auth status
gh api user --jq .login
```

The expected login is `reallife-spark`. If it is not, stop; do not push.

### 2. Create the private repo

The owner may create `interview_app` in the GitHub UI, or the build agent may run
the following after explicit confirmation:

```bash
gh repo create interview_app --private --source=. --remote=origin
```

If the repository already exists:

```bash
git remote add origin https://github.com/reallife-spark/interview_app.git
```

### 3. Add the course remote

```bash
git remote add course https://github.com/TuringCollegeSubmissions/rmobil-AE.1.5.git
git remote -v
```

If the course repository already has an initial commit:

```bash
git fetch course
git rebase course/main
```

If the histories are unrelated and a merge is required, use a normal merge and
resolve conflicts; never force-push without explicit confirmation.

### 4. Push

```bash
git push -u origin main
git push -u course main
```

Verify both GitHub pages. The course repo is the reviewer-visible artifact.
The private repo is the backup.

## Streamlit Community Cloud

### Exact deployment runbook

1. Sign in to <https://share.streamlit.io> with the GitHub account
   `reallife-spark`. A convenience link is
   <https://share.streamlit.io/deploy?repository=reallife-spark/interview_app&branch=main&mainModule=app.py>.
2. Choose **Create app** → **Deploy a public app from GitHub**.
3. Repository: `reallife-spark/interview_app`.
4. Branch: `main`.
5. Main file path: `app.py`.
6. Advanced settings → Python version: **3.12**. The repository also carries
   `runtime.txt` with `python-3.12`.
7. Add these secrets in the Streamlit app settings. Use placeholders locally;
   never commit real values:

   ```toml
   OPENROUTER_API_KEY = "your-key-here"
   OPENROUTER_MODEL = "openai/gpt-6-luna"
   OPENROUTER_TIMEOUT_SECONDS = 60
   MAX_OUTPUT_TOKENS = 1200
   MAX_CALLS = 20
   SESSION_COST_CAP_USD = 0.50
   ```

   The committed template is `.streamlit/secrets.toml.example`.
8. Deploy. Public URL (recorded 2026-11-17):
   <https://interviewap-nbsnftcgrwj7yjcm2h658m.streamlit.app/>.
9. Open the public URL and verify:
   - the page loads without a server error;
   - **Demo** provider works with no network;
   - **OpenRouter** provider works with the secret and can generate a question
     set;
   - one answer evaluation and one Coach message work;
   - off-topic refusal and soft/strict injection behaviour are visible;
   - the last-call cost/tokens/latency and session cap are visible;
   - Markdown/JSON export and Clear session work;
   - no key or job description appears in the page, export or error.

### Deployment preflight commands

```bash
test -f .env && stat -c '.env mode=%a' .env
git check-ignore .env
test -z "$(git ls-files .env)"
PYTHONPATH=src python -c "from interview_practice.config import Settings; s=Settings.from_env(); print(s.provider, s.model, bool(s.openrouter_api_key))"
./scripts/check.sh
```

For the public app, `.env` is not present. Streamlit Cloud reads secrets through
`st.secrets`; the app merges them in `_runtime_settings()`.

### Public smoke status (2026-11-17)

- The URL rendered in headless Chromium from this host; title:
  `Interview Practice Coach · Streamlit`.
- Provider: **`OpenRouter — public`**; model: `openai/gpt-6-luna`.
- Live question set: five questions rendered.
- Live structured answer evaluation rendered, including improved answer and
  next steps.
- Live Coach follow-up rendered.
- Safety: a prompt-injection request was refused; the UI also flagged
  `ignore_previous` and `reveal_prompt` patterns.
- Cost display: calls/session cost/last-call usage visible; the run used four
  calls and about `$0.000841` before clear.
- Export chat (Markdown) downloaded `interview-practice-chat.md`.
- Clear session reset the UI to `Calls 0/20` and `Session cost $0.00`.
- No key-shaped value appeared in the rendered text or export.
- This is an automated headless smoke test on 2026-11-17, not a manual
  reviewer test.
- Re-check on 2026-11-17 at 13:13 UTC: the first hop is a 303 to
  `share.streamlit.io/-/auth/app` with a cleared `streamlit_session`. The
  followed chain is `auth/app` → `.../-/login?payload=...` → app `/` → **200**
  shell, and it sets `_streamlit_csrf` plus `streamlit_session`. This is
  Streamlit's anonymous session bootstrap, not a login gate.
- A fresh headless Chromium session loaded the app and its sidebar. Use
  `scripts/smoke_public_app.sh` to assert the final URL, 200 shell and
  `Interview Practice Coach` title; do not treat the first-hop 303 as a failure.
- Cloud discovery passed at 13:49 UTC: `GET /v1/models` returned 200 from
  `python-requests`, and the `agx64` options appeared in the app.
- Browser completion with `gemma4-2b-131k:latest` returned `READY` and recorded
  `Calls 1/20`. `qwen3-vl-4b-65k:latest` exhausted the 1,200-token cap on
  reasoning (`finish_reason=length`, `completion_tokens=1200`) and returned no
  visible content. A 4,096-token diagnostic did not finish within 300s. The
  provider now reports the finish reason and token count and points to a
  non-thinking model; it never exposes reasoning text.

## agx64 public gateway (2026-11-17)

The VPS gateway is implemented at `https://real-life.dev/v1`; see `VPS.md`.
It exposes only `/healthz`, `/v1/models`, `/v1/chat/completions` and
`/v1/embeddings`. `/v1/*` returns 401 without the server-side bearer token and
200 with it. No direct Ollama port or `/api/*` route is exposed.

Set these in Streamlit Cloud secrets to enable the `agx64` option:

```toml
LOCAL_BASE_URL = "https://real-life.dev/v1"
LOCAL_API_KEY = "the server-side gateway token"
```

The Cloud secret was verified on 2026-11-17 by discovery and a completion from
the public app; no key appeared in the page controls. The gateway checks above
were also run from the build host. Repeatable checks are
`./scripts/smoke_public_app.sh` and
`LOCAL_API_KEY=... ./scripts/smoke_gateway.sh`. The `real-life.dev` card
remains suspended.

## real-life.dev — suspended

The owner directed on 2026-11-17 that no `real-life.dev` deployment or project
card be made. No card was added, no card source is maintained, and no
`real-life.dev` live claim is made. The Streamlit URL is the only public
deployment. This decision supersedes the earlier card suggestion.

## Course submission

1. Confirm the course repo contains the project and history.
2. Click **Submit Project** in the LMS.
3. Schedule a project review. A review cannot be booked with less than 6 hours
   until the timeslot.
4. The reviewer is given access to the course repo. Double-check the correct
   repository before booking.
5. If a second review is needed, make improvements from the first review before
   booking it.

The learner starts with 6 correction points; scheduling costs one point and a
cancellation does not refund it. The LMS page is authoritative.

## Troubleshooting

| Symptom | Check |
|---|---|
| `OPENROUTER_API_KEY is required` | Add the key to `.env` or Streamlit secrets |
| `OpenRouter request failed (401)` | Key is invalid or lacks access |
| `OpenRouter request failed (429)` | Rate limit; wait or lower call frequency |
| Invalid JSON error | Switch to `JSON schema`; retry; do not trust malformed output |
| Local mode fails | Tunnel at `http://127.0.0.1:21464/v1` is down; no fallback |
| Streamlit Cloud cannot reach local mode | Expected; use OpenRouter or demo |
| `git push` rejected | Fetch/rebase; do not force-push without confirmation |
| Course repo has README | Merge or rebase; keep the course repo's history |

## What is not verified here

- The public Streamlit page was smoke-tested in **OpenRouter mode** in headless
  Chromium on 2026-11-17: five-question generation, evaluation, Coach chat,
  safety refusal, cost display, Markdown export and clear all passed.
- A dated OpenRouter evaluation sample was also run locally on 2026-11-17.
- No `real-life.dev` deployment or card was made; it is intentionally suspended.
- No course submission or review was completed.
- The project `.env` is absent; the Cloud secret is configured and the public
  live path passed, but local live runs still need the project `.env`.
- These are user actions with their own credentials and confirmation gates.
