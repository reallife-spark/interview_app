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

Expected on this host (2026-11-16): 69 tests, Ruff 0, 18 evaluation rows,
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

1. Sign in to Streamlit Community Cloud with the GitHub account that can read the
   repository.
2. Create a new app from the repository.
3. Entry point: `app.py`.
4. Add secrets in the Streamlit app settings:

   ```toml
   OPENROUTER_API_KEY = "your-key-here"
   OPENROUTER_MODEL = "openai/gpt-6-luna"
   ```

5. Deploy.
6. Open the public URL and verify:
   - the page loads;
   - Demo mode works without a key;
   - OpenRouter mode works with the key;
   - no key or job description appears in the page text or an export.

Streamlit Cloud cannot reach the local `agx64` tunnel. Local mode is documented
as a developer path only.

## real-life.dev project card

Add a project card that links to the Streamlit URL and the course repository.
The site's exact component was not readable from this host; use the site's
existing card pattern and confirm the result visually.

Suggested content:

- **Title:** Interview Practice Coach
- **Description:** Job-description-tailored AI interview practice with
  structured feedback, six prompt techniques and a defensive prompt.
- **Links:** live app + course repository
- **Tags:** AI engineering, Streamlit, OpenRouter, prompt engineering

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

- No public Streamlit deployment was created from this host.
- No OpenRouter live call was made unless a later dated run records it.
- No `real-life.dev` deployment was made.
- No course submission or review was completed.
- These are user actions with their own credentials and confirmation gates.
