---
title: Handoff — Interview Practice App
updated: 2026-11-16
sources:
  - DEPLOYMENT.md
  - 03_Sources/turing-college/interview-practice-app-brief-2026-11-16.md
tags:
  - handoff
  - github
  - turing-college
---

# Handoff

## Current state

- Project: `/mnt/knowledge/AIengin/06_Projects/interview-practice-app/`
- Private repo: `https://github.com/reallife-spark/interview_app`
- Pushed: `main`; `v0.1.1` is the pre-refactor code tag
- Course remote: `https://github.com/TuringCollegeSubmissions/rmobil-AE.1.5.git`
- Course alias `rmobil` is a public GitHub user (`Mobil`); the active `gh`
  account is `reallife-spark`.
- Checks: 100+ tests, Ruff 0, 8 import-linter contracts, headless Streamlit HTTP
  200, vault validation passes.
- Evaluation: 18-row offline fixture (`json_schema` 9.62) and an 18/18-valid live sample on 2026-11-17 (`cot` 9.45).
- Public deployment: <https://interviewap-nbsnftcgrwj7yjcm2h658m.streamlit.app/>.
  A fresh headless Chromium session loaded the app and sidebar on 2026-11-17.
  `curl` gets a first-hop 303 as Streamlit bootstraps an anonymous session;
  `scripts/smoke_public_app.sh` follows it and checks the app title. Cloud
  `agx64` discovery and a `gemma4-2b-131k:latest` completion passed;
  `qwen3-vl-4b-65k:latest` returned empty content because reasoning consumed
  the 1,200-token cap (`finish_reason=length`, `completion_tokens=1200`); a
  4,096-token diagnostic did not finish within 300s. The direct gateway
  completion passed. The provider now reports the cap and finish reason without
  exposing reasoning text. OpenRouter was
  smoke-tested in headless Chromium on 2026-11-17: live five-question set,
  evaluation, Coach chat, injection refusal, cost display, Markdown export and
  clear all passed. No key was visible. See `DEPLOYMENT.md`.
- Project `.env`: absent; the vault-root `.env` is not read. Add the rotated key
  to the project `.env` for local live runs, or to Streamlit Cloud secrets.
- Gateway: `https://real-life.dev/v1` is implemented; WireGuard handshake and
  public 401/200 checks passed on 2026-11-17. Streamlit Cloud
  `LOCAL_BASE_URL` and `LOCAL_API_KEY` were verified via discovery and a
  completion on 2026-11-17.

## Verification record: public app

| Check | Result |
|---|---|
| Streamlit Cloud gateway secret | Verified 2026-11-17 by `agx64` discovery and a `gemma4-2b-131k:latest` completion |
| Streamlit app sharing | Fresh browser load passed; first-hop `curl` 303 is Streamlit's anonymous session bootstrap |
| Browser smoke | `agx64` discovery and completion passed; thinking model direct check passed |
| Key safety | No key visible in page controls or exports |
| Course/card | Still do not push `course`; do not add a `real-life.dev` card |

## Current blocker

`git ls-remote course` returns:

```text
remote: Write access to repository not granted.
fatal: unable to access 'https://github.com/TuringCollegeSubmissions/rmobil-AE.1.5.git/': The requested URL returned error: 403
```

`gh repo view TuringCollegeSubmissions/rmobil-AE.1.5` cannot resolve the
repository. Re-checked on 2026-11-16:

- `gh auth status` active account: `reallife-spark`
- `git ls-remote course`: HTTP 403
- `gh api repos/TuringCollegeSubmissions/rmobil-AE.1.5`: HTTP 404
- `curl` to the repository page: HTTP 404

The private `interview_app` repo is pushed, but the course mirror is not. The
repository alias `rmobil` and the active `reallife-spark` login may be different
GitHub identities. Authenticate `gh` as the student account, or click the LMS
GitHub icon to create/authorize the repository. Do not push to a different
account blindly and do not force-push.

## User action: course repository

1. Open the Turing College LMS project page.
2. Click the GitHub icon for the project. The LMS should show the
   student-specific repository URL.
3. If the URL differs from `rmobil-AE.1.5`, update the `course` remote.
4. Authorize `TuringCollegeSubmissions` if the LMS asks.
5. Authenticate `gh` as the student account `rmobil` (the alias in the course
   URL), not `reallife-spark`:

   ```bash
   gh auth login --hostname github.com --git-protocol https
   # choose "Login with a web browser" and sign in as rmobil
   gh auth status
   gh api user --jq .login
   ```

   The private `interview_app` repo was already pushed as `reallife-spark`; use
   `rmobil` only for the course push, or switch back after.

6. Re-check access without writing:

   ```bash
   git ls-remote course
   ```

7. If the course repo has an initial commit:

   ```bash
   git fetch course
   git rebase course/main
   ```

   If the histories are unrelated, merge and resolve conflicts normally.

8. Push:

   ```bash
   git push -u course main
   ```

9. Refresh the course repository page and confirm the files are present.
10. Only then click **Submit Project** and schedule the review.

## If the course URL changes

```bash
git remote set-url course <new-course-url>
git ls-remote course
git push -u course main
```

## What not to do

- Do not read or echo `.env`.
- Do not commit `.env`, `.venv`, keys or tokens.
- Do not force-push.
- Do not push to the course repo before access is verified.
- Do not claim a manual reviewer test or a completed course review. The public
  OpenRouter path was smoke-tested on 2026-11-17; the course mirror is still
  blocked.

## After the course push

- Update `DEPLOYMENT.md` and the LMS evidence with the actual course URL.
- The Streamlit Cloud secret was verified by discovery and completion on
  2026-11-17; the public live smoke passed.
- Do not add or claim a `real-life.dev` card; the owner suspended it on
  2026-11-17.
- Submit and schedule the review.
